"""
Automated Unit and Integration Tests for KDS System:
- Database creation & seeding
- Hardware constraint verification (8GB RAM elimination for gaming, portability kısıtı < 2.0kg)
- Intersection logic (Oyun + Yazılım)
- 60% barajı and elimination reasons
- Phone & tablet evaluation
- REST API integration
- ETL normalization
"""
import os
import unittest
import tempfile
import json

from kds.database import init_db, fetch_all_devices, insert_device, upsert_device, delete_device, get_last_sync_info
from kds.decision_engine import evaluate_devices, synthesize_laptop_weights
from etl.import_devices import clean_and_normalize_record, run_etl
from etl.daily_sync import run_daily_sync
from app import app


class TestKDSSystem(unittest.TestCase):
    def setUp(self):
        self.temp_db_fd, self.temp_db_path = tempfile.mkstemp(suffix=".db")
        init_db(self.temp_db_path, force_reset=True)
        self.app_client = app.test_client()

    def tearDown(self):
        os.close(self.temp_db_fd)
        if os.path.exists(self.temp_db_path):
            os.remove(self.temp_db_path)

    def test_seed_data_count_and_categories(self):
        """Verifies database contains at least 18-24 realistic devices across all 3 categories."""
        devices = fetch_all_devices(self.temp_db_path)
        self.assertGreaterEqual(len(devices), 24, "En az 24 örnek cihaz bulunmalıdır.")

        laptops = [d for d in devices if d["category"] == "laptop"]
        phones = [d for d in devices if d["category"] == "phone"]
        tablets = [d for d in devices if d["category"] == "tablet"]

        self.assertGreaterEqual(len(laptops), 12, "En az 12 laptop bulunmalı.")
        self.assertGreaterEqual(len(phones), 6, "En az 6 telefon bulunmalı.")
        self.assertGreaterEqual(len(tablets), 6, "En az 6 tablet bulunmalı.")

        # Check for 8GB RAM laptops in seed
        eight_gb_laptops = [l for l in laptops if l["ram_gb"] == 8]
        self.assertGreaterEqual(len(eight_gb_laptops), 3, "8 GB RAM'li giriş laptopları bulunmalıdır.")

        # Check for < 2.0 kg lightweight laptops in seed
        light_laptops = [l for l in laptops if l["weight_kg"] and l["weight_kg"] < 2.0]
        self.assertGreaterEqual(len(light_laptops), 4, "Hafif (< 2.0 kg) laptoplar bulunmalıdır.")

    def test_gaming_hard_constraint_eliminates_8gb_ram(self):
        """When Oyun is selected, ram_gb < 16 MUST be eliminated by hard constraint."""
        devices = fetch_all_devices(self.temp_db_path, category="laptop")
        res = evaluate_devices(
            devices=devices,
            category="laptop",
            budget=80000.0,
            purposes=["oyun"],
            weight_bands=["hafif", "orta", "agir"]
        )

        # Ensure no recommended device has < 16 GB RAM
        for rec in res["recommended"]:
            self.assertGreaterEqual(rec["ram_gb"], 16, f"{rec['model']} Oyun için önerildi ancak RAM < 16!")

        # Find 8 GB RAM laptops in eliminated list
        elim_ram_reasons = [e for e in res["eliminated"] if "RAM" in e.get("reason", "") and "Oyun" in e.get("reason", "")]
        self.assertGreater(len(elim_ram_reasons), 0, "8 GB RAM'li cihazlar Oyun gerekçesiyle elenmeli.")

    def test_portability_constraint_under_2kg(self):
        """If only Hafif (< 2.0 kg) is selected, devices >= 2.0 kg must be eliminated."""
        devices = fetch_all_devices(self.temp_db_path, category="laptop")
        res = evaluate_devices(
            devices=devices,
            category="laptop",
            budget=90000.0,
            purposes=["gunluk"],
            weight_bands=["hafif"]
        )

        for rec in res["recommended"]:
            self.assertLess(rec["weight_kg"], 2.0, f"{rec['model']} hafif seçilmesine rağmen 2.0 kg ve üzeri!")

        # Heavy laptops like Legion or Nitro must be eliminated with weight reason
        elim_weights = [e for e in res["eliminated"] if "hafif" in e.get("reason", "").lower() or "ağırlık" in e.get("reason", "").lower()]
        self.assertGreater(len(elim_weights), 0, "2.0 kg üzerindeki cihazlar hafiflik kısıtıyla elenmeli.")

    def test_intersection_gaming_and_software_dev(self):
        """When both Oyun and Yazılım are selected, intersection criteria and combined weights are applied."""
        devices = fetch_all_devices(self.temp_db_path, category="laptop")
        res = evaluate_devices(
            devices=devices,
            category="laptop",
            budget=90000.0,
            purposes=["oyun", "yazilim"],
            weight_bands=["hafif", "orta", "agir"]
        )

        # Check weights are dynamically synthesized
        weights = res["weights_used"]
        self.assertIn("cpu", weights)
        self.assertIn("gpu", weights)
        self.assertIn("ram", weights)
        self.assertGreater(weights["cpu"], 0.20, "Yazılım geliştirme CPU ağırlığını yükseltmeli.")
        self.assertGreater(weights["gpu"], 0.15, "Oyun GPU ağırlığını korumalı.")

        # Every recommended device must meet intersection: ram >= 16, cpu >= 70, gpu >= 65, storage >= 512
        for rec in res["recommended"]:
            self.assertGreaterEqual(rec["ram_gb"], 16)
            self.assertGreaterEqual(rec["cpu_score"], 70)
            self.assertGreaterEqual(rec["gpu_score"], 65)
            self.assertGreaterEqual(rec["storage_gb"], 512)

    def test_sixty_percent_threshold(self):
        """No recommended device has suitability score < 60%."""
        devices = fetch_all_devices(self.temp_db_path, category="laptop")
        res = evaluate_devices(
            devices=devices,
            category="laptop",
            budget=50000.0,
            purposes=["gunluk"]
        )

        for rec in res["recommended"]:
            self.assertGreaterEqual(rec["suitability_score"], 60.0)

        for elim in res["eliminated"]:
            if elim.get("elimination_type") == "score_below_threshold":
                self.assertLess(elim["suitability_score"], 60.0)

    def test_phone_and_tablet_evaluation(self):
        """Phone and tablet categories evaluate successfully with standard KDS profiles."""
        devices = fetch_all_devices(self.temp_db_path)

        res_phone = evaluate_devices(
            devices=devices,
            category="phone",
            budget=75000.0
        )
        self.assertGreater(len(res_phone["recommended"]), 0)

        res_tablet = evaluate_devices(
            devices=devices,
            category="tablet",
            budget=45000.0
        )
        self.assertGreater(len(res_tablet["recommended"]), 0)

    def test_missing_data_reporting(self):
        """Missing critical fields are reported with reason, not silently swallowed."""
        bad_devices = [
            {
                "id": 999,
                "category": "laptop",
                "brand": "Test",
                "model": "Broken Device",
                "price_try": None,  # Missing price
                "cpu_score": 80,
                "gpu_score": 80,
                "battery_score": 80,
                "display_score": 80,
                "camera_or_stylus_score": 80,
                "storage_gb": 512
            }
        ]
        res = evaluate_devices(bad_devices, category="laptop", budget=50000.0)
        self.assertEqual(len(res["recommended"]), 0)
        self.assertEqual(len(res["eliminated"]), 1)
        self.assertIn("Fiyat", res["eliminated"][0]["reason"])

    def test_rest_api_endpoints(self):
        """Tests REST API endpoints."""
        # GET /api/devices
        res = self.app_client.get("/api/devices")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["status"], "success")

        # POST /api/devices
        new_dev = {
            "category": "laptop",
            "brand": "TestBrand",
            "model": "Model X1",
            "price_try": 35000.0,
            "ram_gb": 16,
            "storage_gb": 512,
            "weight_kg": 1.45,
            "cpu_name": "Intel Core i7-13650HX",
            "gpu_name": "RTX 4060",
            "battery_score": 75,
            "display_score": 85,
            "camera_or_stylus_score": 70
        }
        res_post = self.app_client.post("/api/devices", json=new_dev)
        self.assertEqual(res_post.status_code, 201)
        created_id = res_post.get_json()["device"]["id"]

        # DELETE /api/devices/<id>
        res_del = self.app_client.delete(f"/api/devices/{created_id}")
        self.assertEqual(res_del.status_code, 200)

        # POST /api/evaluate
        eval_payload = {
            "category": "laptop",
            "budget": 55000,
            "purposes": ["oyun"],
            "weight_bands": ["hafif", "orta", "agir"]
        }
        res_eval = self.app_client.post("/api/evaluate", json=eval_payload)
        self.assertEqual(res_eval.status_code, 200)
        self.assertIn("recommended", res_eval.get_json()["evaluation"])

    def test_etl_normalization_and_scoring(self):
        """Verifies ETL CPU/GPU scoring and price cleaning."""
        raw = {
            "category": "notebook",
            "brand": "Alienware",
            "model": "m16 R2",
            "price_try": "74.999,00 TL",
            "ram_gb": "32 GB",
            "storage_gb": "1 TB",
            "weight_kg": "2.61 kg",
            "cpu_name": "Intel Core Ultra 7 155H",
            "gpu_name": "NVIDIA GeForce RTX 4070",
        }
        cleaned = clean_and_normalize_record(raw)
        self.assertEqual(cleaned["category"], "laptop")
        self.assertEqual(cleaned["price_try"], 74999.0)
        self.assertEqual(cleaned["ram_gb"], 32)
        self.assertEqual(cleaned["storage_gb"], 1024)
        self.assertEqual(cleaned["weight_kg"], 2.61)
        self.assertGreaterEqual(cleaned["cpu_score"], 80)
        self.assertGreaterEqual(cleaned["gpu_score"], 85)

    def test_upsert_logic(self):
        """Verifies UPSERT updates existing device without duplicate creation."""
        test_device = {
            "category": "laptop",
            "brand": "TestBrand",
            "model": "UpsertPro",
            "price_try": 40000.0,
            "ram_gb": 16,
            "storage_gb": 512,
            "weight_kg": 1.5,
            "cpu_name": "Intel Core i7-13650HX",
            "gpu_name": "RTX 4060",
            "cpu_score": 85,
            "gpu_score": 80,
            "battery_score": 75,
            "display_score": 85,
            "camera_or_stylus_score": 70
        }
        dev_id1, op1 = upsert_device(test_device, self.temp_db_path)
        self.assertEqual(op1, "inserted")

        # Update with new price and more RAM
        test_device["price_try"] = 43500.0
        test_device["ram_gb"] = 32
        dev_id2, op2 = upsert_device(test_device, self.temp_db_path)
        self.assertEqual(op2, "updated")
        self.assertEqual(dev_id1, dev_id2, "Aynı cihaz ID'si güncellenmelidir.")

        # Verify in DB
        devices = fetch_all_devices(self.temp_db_path)
        matched = [d for d in devices if d["brand"] == "TestBrand" and d["model"] == "UpsertPro"]
        self.assertEqual(len(matched), 1, "Cihaz mükerrer eklenmemelidir.")
        self.assertEqual(matched[0]["price_try"], 43500.0)
        self.assertEqual(matched[0]["ram_gb"], 32)
        self.assertIsNotNone(matched[0]["last_synced_at"])

    def test_daily_sync_execution_and_logging(self):
        """Verifies run_daily_sync executes with fallback and logs to sync_logs table."""
        res = run_daily_sync(force_backup=True, db_path=self.temp_db_path)
        self.assertEqual(res["status"], "success")
        self.assertGreater(res["records_fetched"], 0)

        # Check sync_logs table
        last_log = get_last_sync_info(self.temp_db_path)
        self.assertIsNotNone(last_log)
        self.assertEqual(last_log["status"], "SUCCESS")
        self.assertGreater(last_log["records_fetched"], 0)

    def test_sync_rest_api_endpoints(self):
        """Verifies GET /api/sync/status and POST /api/sync/live."""
        res_status = self.app_client.get("/api/sync/status")
        self.assertEqual(res_status.status_code, 200)
        data_status = res_status.get_json()
        self.assertEqual(data_status["status"], "success")
        self.assertIn("schedule", data_status)

        res_live = self.app_client.post("/api/sync/live?force_backup=true")
        self.assertEqual(res_live.status_code, 200)
        data_live = res_live.get_json()
        self.assertEqual(data_live["status"], "success")
        self.assertIn("sync_result", data_live)


if __name__ == "__main__":
    unittest.main()

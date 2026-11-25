"""
Akıllı Donanım ve Cihaz Seçim Sistemi - KDS Web Uygulaması ve REST API
Decision Support System (KDS / DSS) Web Application with SQLite Backend
"""
import os
import json
import csv
import io
import threading
import time
from datetime import datetime
from flask import Flask, request, jsonify, render_template, send_from_directory

from kds.database import (
    init_db,
    fetch_all_devices,
    insert_device,
    delete_device,
    get_last_sync_info,
    get_sync_history,
    DEFAULT_DB_PATH
)
from kds.decision_engine import evaluate_devices
from etl.import_devices import clean_and_normalize_record
from etl.daily_sync import run_daily_sync

app = Flask(__name__, static_folder="static", template_folder="templates")

# Initialize SQLite database on startup
DB_PATH = os.environ.get("KDS_DB_PATH", DEFAULT_DB_PATH)
init_db(DB_PATH)


def background_daily_scheduler(target_hour: int = 9, target_minute: int = 0):
    """
    Lightweight in-app daemon thread that triggers daily sync at target_hour:target_minute.
    Runs once per day without blocking the web server.
    """
    last_synced_day = None
    print(f"[*] [KDS Scheduler] Zamanlayıcı devrede: Her gün saat {target_hour:02d}:{target_minute:02d}'da otomatik çalışacak.")
    while True:
        try:
            now = datetime.now()
            if now.hour == target_hour and now.minute == target_minute and last_synced_day != now.date():
                print(f"[+] [KDS Scheduler] Saat {target_hour:02d}:{target_minute:02d} geldi. Otomatik günlük senkronizasyon yürütülüyor...")
                run_daily_sync(db_path=DB_PATH)
                last_synced_day = now.date()
        except Exception as e:
            print(f"[-] [KDS Scheduler] Günlük zamanlayıcı hatası: {e}")
        time.sleep(30)


# Start background daily scheduler thread
scheduler_thread = threading.Thread(target=background_daily_scheduler, args=(9, 0), daemon=True)
scheduler_thread.start()


@app.route("/")
def index():
    """Serves the academic decision support web interface."""
    return render_template("index.html")


@app.route("/api/info", methods=["GET"])
def api_info():
    """Returns database summary, system status, and last live sync info."""
    devices = fetch_all_devices(DB_PATH)
    laptops = [d for d in devices if d["category"] == "laptop"]
    phones = [d for d in devices if d["category"] == "phone"]
    tablets = [d for d in devices if d["category"] == "tablet"]
    last_sync = get_last_sync_info(DB_PATH)

    return jsonify({
        "status": "online",
        "system_name": "Akıllı Donanım ve Cihaz Seçim Sistemi (KDS)",
        "last_sync": last_sync,
        "database": {
            "type": "SQLite",
            "path": DB_PATH,
            "total_devices": len(devices),
            "counts": {
                "laptop": len(laptops),
                "phone": len(phones),
                "tablet": len(tablets)
            }
        }
    })


@app.route("/api/sync/live", methods=["POST"])
def trigger_live_sync():
    """
    Triggers an immediate live sync on demand ("Şimdi Canlı Güncelle").
    Fetches live/backup feed, normalizes, executes UPSERT into SQLite, and returns stats.
    """
    try:
        force_backup = request.args.get("force_backup", "false").lower() == "true"
        result = run_daily_sync(db_path=DB_PATH, force_backup=force_backup)
        last_sync = get_last_sync_info(DB_PATH)
        devices = fetch_all_devices(DB_PATH)
        return jsonify({
            "status": "success",
            "message": "Canlı veri senkronizasyonu başarıyla tamamlandı.",
            "sync_result": result,
            "last_sync": last_sync,
            "total_devices": len(devices)
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Senkronizasyon hatası: {str(e)}"
        }), 500


@app.route("/api/sync/status", methods=["GET"])
def get_sync_status():
    """Returns last sync status, history logs, and schedule configuration."""
    last_sync = get_last_sync_info(DB_PATH)
    history = get_sync_history(limit=5, db_path=DB_PATH)
    return jsonify({
        "status": "success",
        "schedule": "Günde 1 Kez (Her gün 09:00)",
        "last_sync": last_sync,
        "history": history
    })


@app.route("/api/devices", methods=["GET"])
def get_devices():
    """Lists devices, optionally filtered by category query param (?category=laptop|phone|tablet)."""
    category = request.args.get("category")
    if category:
        category = category.lower().strip()
    devices = fetch_all_devices(DB_PATH, category=category)
    return jsonify({
        "status": "success",
        "count": len(devices),
        "devices": devices
    })


@app.route("/api/devices", methods=["POST"])
def create_device():
    """Creates a new device in SQLite."""
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"status": "error", "message": "Geçersiz JSON verisi."}), 400

    # Required fields validation
    required = ["category", "brand", "model", "price_try", "storage_gb", "cpu_name", "gpu_name"]
    missing = [f for f in required if f not in data or data[f] in (None, "")]
    if missing:
        return jsonify({
            "status": "error",
            "message": f"Eksik zorunlu alanlar: {', '.join(missing)}"
        }), 400

    try:
        normalized = clean_and_normalize_record(data)
        new_id = insert_device(normalized, DB_PATH)
        normalized["id"] = new_id
        return jsonify({
            "status": "success",
            "message": "Cihaz SQLite veritabanına başarıyla eklendi.",
            "device": normalized
        }), 201
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/devices/<int:device_id>", methods=["DELETE"])
def remove_device(device_id: int):
    """Deletes a device from SQLite by ID."""
    deleted = delete_device(device_id, DB_PATH)
    if deleted:
        return jsonify({
            "status": "success",
            "message": f"ID {device_id} nolu cihaz başarıyla silindi."
        })
    else:
        return jsonify({
            "status": "error",
            "message": f"ID {device_id} nolu cihaz veritabanında bulunamadı."
        }), 404


@app.route("/api/devices/import", methods=["POST"])
def import_devices():
    """
    Bulk import devices from JSON array or CSV payload.
    Supports:
    1. Direct JSON array: [ { ... }, { ... } ]
    2. JSON object with "devices": [ ... ]
    3. JSON object with "format": "csv", "data": "csv text..."
    """
    payload = request.get_json(silent=True)
    if not payload:
        return jsonify({"status": "error", "message": "Geçersiz veya boş istek gövdesi."}), 400

    raw_items = []
    if isinstance(payload, list):
        raw_items = payload
    elif isinstance(payload, dict):
        if "devices" in payload and isinstance(payload["devices"], list):
            raw_items = payload["devices"]
        elif payload.get("format") == "csv" and "data" in payload:
            csv_text = payload["data"]
            reader = csv.DictReader(io.StringIO(csv_text))
            raw_items = [row for row in reader]
        elif payload.get("format") == "json" and "data" in payload:
            raw_items = json.loads(payload["data"])
        else:
            raw_items = [payload]

    if not raw_items:
        return jsonify({"status": "error", "message": "İçe aktarılacak geçerli kayıt bulunamadı."}), 400

    inserted_count = 0
    errors = []

    for index, raw in enumerate(raw_items):
        try:
            cleaned = clean_and_normalize_record(raw)
            insert_device(cleaned, DB_PATH)
            inserted_count += 1
        except Exception as e:
            errors.append(f"Kayıt #{index+1} eklenemedi: {str(e)}")

    return jsonify({
        "status": "success",
        "message": f"{inserted_count} cihaz başarıyla SQLite veritabanına aktarıldı.",
        "inserted_count": inserted_count,
        "failed_count": len(errors),
        "errors": errors
    })


@app.route("/api/reset", methods=["POST"])
def reset_database():
    """Resets the SQLite database to realistic seed data (27 devices)."""
    count = init_db(DB_PATH, force_reset=True)
    return jsonify({
        "status": "success",
        "message": f"SQLite veritabanı başarıyla sıfırlandı ve {count} cihazlık örnek veri seti yüklendi.",
        "device_count": count
    })


@app.route("/api/evaluate", methods=["POST"])
def evaluate():
    """
    KDS Decision Support Evaluation endpoint.
    Payload:
    {
        "category": "laptop" | "phone" | "tablet",
        "budget": 45000,
        "purposes": ["oyun", "yazilim"],
        "weight_bands": ["hafif"],
        "budget_tolerance": 0.05,
        "custom_weights": { ... } (optional)
    }
    """
    data = request.get_json(silent=True) or {}
    category = data.get("category", "laptop")
    budget = float(data.get("budget", 50000.0))
    purposes = data.get("purposes", ["gunluk"])
    weight_bands = data.get("weight_bands", ["hafif", "orta", "agir"])
    budget_tolerance = float(data.get("budget_tolerance", 0.05))
    custom_weights = data.get("custom_weights")

    devices = fetch_all_devices(DB_PATH, category=category)
    result = evaluate_devices(
        devices=devices,
        category=category,
        budget=budget,
        purposes=purposes,
        weight_bands=weight_bands,
        budget_tolerance=budget_tolerance,
        custom_weights=custom_weights
    )

    return jsonify({
        "status": "success",
        "evaluation": result
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"[*] KDS Akıllı Donanım Seçim Sistemi http://127.0.0.1:{port} adresinde çalışıyor...")
    app.run(host="0.0.0.0", port=port, debug=True)

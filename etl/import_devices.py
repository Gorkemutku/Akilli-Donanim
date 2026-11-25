"""
ETL Pipeline for KDS Device Import.
Cleans raw JSON/CSV feeds, derives 0-100 KDS benchmark scores from CPU/GPU hardware names,
and ingests clean records into the SQLite devices table.
"""
import re
import os
import sys
import csv
import json
import sqlite3
import argparse
from typing import List, Dict, Any, Tuple, Optional

# CPU scoring dictionary & regex rules
CPU_RULES: List[Tuple[str, int]] = [
    # Apple Silicon
    (r"m4\s*max", 99),
    (r"m4\s*pro", 98),
    (r"m4", 97),
    (r"m3\s*max", 96),
    (r"m3\s*pro", 93),
    (r"m3", 86),
    (r"m2\s*pro", 89),
    (r"m2", 84),
    (r"m1\s*pro", 85),
    (r"m1", 79),
    (r"a17\s*pro", 96),
    (r"a16\s*bionic", 91),
    (r"a15\s*bionic", 84),
    (r"a14\s*bionic", 72),

    # Intel Laptop / Desktop
    (r"i9[- ]14900", 98),
    (r"i9[- ]13900", 96),
    (r"i7[- ]14700", 94),
    (r"i7[- ]13700|i7[- ]13650", 88),
    (r"i7[- ]13620|i7[- ]1360", 82),
    (r"core ultra 9", 93),
    (r"core ultra 7", 86),
    (r"core ultra 5", 81),
    (r"i5[- ]13500|i5[- ]13420", 76),
    (r"i5[- ]1235|i5[- ]12450", 63),
    (r"i3[- ]1215", 52),
    (r"celeron|pentium", 35),

    # AMD Laptop / Desktop
    (r"ryzen 9\s*7945", 98),
    (r"ryzen 7\s*7840|ryzen 7\s*7745|ryzen 7\s*8845", 91),
    (r"ryzen 5\s*7640|ryzen 5\s*7535", 78),
    (r"ryzen 5\s*7520|ryzen 5\s*5500", 58),
    (r"ryzen 3\s*7320", 48),

    # Mobile SoC (Qualcomm, MediaTek, Samsung, Google)
    (r"snapdragon 8\s*gen 3", 95),
    (r"snapdragon 8\s*gen 2", 90),
    (r"snapdragon 8\s*gen 1", 82),
    (r"snapdragon 870|snapdragon 888", 76),
    (r"snapdragon 7\s*gen", 75),
    (r"dimensity 9300", 94),
    (r"dimensity 8300", 86),
    (r"dimensity 7200", 74),
    (r"dimensity 7050", 66),
    (r"tensor g3", 84),
    (r"tensor g2", 78),
    (r"exynos 2400", 91),
    (r"exynos 1480", 68),
    (r"exynos 1380", 63),
]

# GPU scoring dictionary & regex rules
GPU_RULES: List[Tuple[str, int]] = [
    # High-end Gaming RTX
    (r"rtx\s*4090", 99),
    (r"rtx\s*4080", 95),
    (r"rtx\s*4070", 89),
    (r"rtx\s*4060", 82),
    (r"rtx\s*4050", 71),
    (r"rtx\s*3080", 84),
    (r"rtx\s*3070", 78),
    (r"rtx\s*3060", 73),
    (r"rtx\s*3050", 61),
    (r"rtx\s*2050", 54),

    # Apple GPU
    (r"m4\s*max", 98),
    (r"m4\s*pro", 92),
    (r"m4\s*gpu|apple m4", 88),
    (r"m3\s*max", 95),
    (r"m3\s*pro\s*gpu", 80),
    (r"m3\s*gpu|apple m3", 64),
    (r"m2\s*gpu|apple m2", 58),
    (r"a17\s*pro\s*gpu", 94),
    (r"a16\s*gpu", 85),
    (r"a15\s*gpu", 78),

    # Integrated & Mobile GPUs
    (r"adreno 750", 93),
    (r"adreno 740", 86),
    (r"adreno 730", 78),
    (r"adreno 650|adreno 660", 72),
    (r"mali[- ]g610|mali[- ]g68", 68),
    (r"immortalis", 82),
    (r"xclipse 530", 62),
    (r"intel arc", 55),
    (r"radeon 780m", 57),
    (r"radeon 680m", 51),
    (r"iris xe", 44),
    (r"uhd graphics", 30),
    (r"radeon 610m|vega", 32),
]


def estimate_cpu_score(cpu_name: str) -> int:
    """Estimates a 0-100 KDS CPU score based on name string."""
    if not cpu_name:
        return 50
    name_clean = cpu_name.lower()
    for pattern, score in CPU_RULES:
        if re.search(pattern, name_clean):
            return score
    return 60  # Default fallback


def estimate_gpu_score(gpu_name: str) -> int:
    """Estimates a 0-100 KDS GPU score based on name string."""
    if not gpu_name:
        return 45
    name_clean = gpu_name.lower()
    for pattern, score in GPU_RULES:
        if re.search(pattern, name_clean):
            return score
    return 50  # Default fallback


def clean_price(price_input: Any) -> float:
    """Cleans numeric or string price (e.g. '45.000,00 TL', '79.500 TL', '45000' -> 45000.0)."""
    if price_input is None:
        return 0.0
    if isinstance(price_input, (int, float)):
        return float(price_input)

    s = (
        str(price_input)
        .strip()
        .replace("TL", "")
        .replace("₺", "")
        .replace("$", "")
        .replace("EUR", "")
        .replace("TRY", "")
        .replace(" ", "")
    )

    # If both . and , exist (e.g. 45.000,50 or 45,000.50)
    if "." in s and "," in s:
        if s.rfind(",") > s.rfind("."):
            s = s.replace(".", "").replace(",", ".")
        else:
            s = s.replace(",", "")
    elif "." in s and "," not in s:
        parts = s.split(".")
        # If parts after dot have length 3 (e.g. 45.000 or 1.250.000) -> thousand separator
        if len(parts) > 1 and all(len(p) == 3 for p in parts[1:]):
            s = s.replace(".", "")
    elif "," in s and "." not in s:
        parts = s.split(",")
        if len(parts) > 1 and all(len(p) == 3 for p in parts[1:]):
            s = s.replace(",", "")
        elif len(parts) == 2 and len(parts[1]) in (1, 2):
            s = s.replace(",", ".")
        else:
            s = s.replace(",", "")

    try:
        return float(s)
    except ValueError:
        return 0.0


KNOWN_BRANDS = [
    "Apple", "Lenovo", "ASUS", "Asus", "HP", "MSI", "Dell", "Acer", "Samsung",
    "Xiaomi", "Google", "OnePlus", "Huawei", "Razer", "Microsoft", "Sony",
    "LG", "Honor", "Monster", "Casper", "Alienware", "Framework"
]


def clean_and_normalize_record(raw: Dict[str, Any]) -> Dict[str, Any]:
    """
    Cleans raw dictionary from diverse external JSON feeds into validated schema dictionary.
    Handles varied key names, robustly normalizes units (TB, GB, g, kg),
    estimates missing KDS hardware scores, and preserves None for missing weight.
    """
    # 1. Model / Title Detection
    model = (
        raw.get("model") or raw.get("title") or raw.get("name") or
        raw.get("product_name") or raw.get("device_name") or raw.get("urun_adi") or "Cihaz"
    )
    model = str(model).strip()

    # 2. Brand Detection
    brand_raw = (
        raw.get("brand") or raw.get("make") or raw.get("manufacturer") or
        raw.get("vendor") or raw.get("marka") or raw.get("uretici")
    )
    if brand_raw and str(brand_raw).strip() not in ("", "null", "None"):
        brand = str(brand_raw).strip()
    else:
        # Infer brand from model / title
        brand = "Bilinmeyen"
        for kb in KNOWN_BRANDS:
            if model.lower().startswith(kb.lower()):
                brand = kb
                break

    # 3. Category Detection & Normalization
    cat_raw = (
        raw.get("category") or raw.get("type") or raw.get("device_type") or
        raw.get("kategori") or raw.get("tur")
    )
    cat_str = str(cat_raw or "").lower().strip()

    if cat_str in ("laptop", "laptops", "notebook", "notebooks", "dizustu", "bilgisayar", "ultrabook", "pc", "computer"):
        category = "laptop"
    elif cat_str in ("phone", "phones", "smartphone", "smartphones", "akillitelefon", "telefon", "mobile", "ceptelefonu"):
        category = "phone"
    elif cat_str in ("tablet", "tablets", "pad", "ipad"):
        category = "tablet"
    else:
        # Infer category from model or brand text
        combined_text = f"{brand} {model}".lower()
        if any(k in combined_text for k in ("iphone", "galaxy s", "galaxy a", "galaxy z", "pixel", "redmi", "xiaomi 1", "oneplus", "xperia", "phone")):
            category = "phone"
        elif any(k in combined_text for k in ("ipad", "galaxy tab", "tab s", "tab p", "tab a", "xiaomi pad", "surface pro", "tablet")):
            category = "tablet"
        elif any(k in combined_text for k in ("macbook", "thinkpad", "legion", "zenbook", "vivobook", "nitro", "omen", "katana", "blade", "gram", "aspire", "ideapad", "laptop", "notebook")):
            category = "laptop"
        else:
            category = "laptop"

    # 4. Price Parsing
    price_val = (
        raw.get("price_try") or raw.get("price") or raw.get("cost") or
        raw.get("fiyat") or raw.get("amount") or raw.get("fiyati") or 0.0
    )
    price_try = clean_price(price_val)

    # 5. RAM Parsing (GB)
    ram_raw = (
        raw.get("ram_gb") or raw.get("ram") or raw.get("memory") or
        raw.get("ram_memory") or raw.get("bellek")
    )
    ram_gb = None
    if ram_raw not in (None, "", "null", "None"):
        try:
            ram_str = str(ram_raw).lower()
            m = re.search(r"(\d+)", ram_str)
            if m:
                val = int(m.group(1))
                if "mb" in ram_str and val >= 1024:
                    val = val // 1024
                ram_gb = val
        except Exception:
            ram_gb = None

    # 6. Storage Parsing (GB)
    storage_raw = (
        raw.get("storage_gb") or raw.get("storage") or raw.get("disk") or
        raw.get("ssd") or raw.get("hdd") or raw.get("rom") or
        raw.get("depolama") or raw.get("capacity")
    )
    default_storage = 512 if category == "laptop" else 128
    storage_gb = default_storage
    if storage_raw not in (None, "", "null", "None"):
        try:
            s_str = str(storage_raw).lower()
            m = re.search(r"(\d+)", s_str)
            if m:
                num = int(m.group(1))
                if "tb" in s_str:
                    num = num * 1024
                elif "mb" in s_str and num >= 1024:
                    num = num // 1024
                storage_gb = num
        except Exception:
            storage_gb = default_storage

    # 7. Weight Parsing (kg) - Preserves None if missing!
    weight_raw = (
        raw.get("weight_kg") or raw.get("weight") or raw.get("agirlik") or
        raw.get("mass")
    )
    weight_kg = None
    if weight_raw not in (None, "", "null", "None"):
        try:
            w_str = str(weight_raw).lower().replace("kg", "").replace("gr", "").replace("g", "").strip().replace(",", ".")
            w_val = float(w_str)
            if w_val > 50:  # Value was given in grams (e.g. 220g -> 0.22kg, 1850g -> 1.85kg)
                w_val = w_val / 1000.0
            if w_val > 0:
                weight_kg = round(w_val, 2)
        except Exception:
            weight_kg = None

    # 8. CPU & GPU Names
    cpu_name = str(
        raw.get("cpu_name") or raw.get("cpu") or raw.get("processor") or
        raw.get("islemci") or raw.get("chipset") or raw.get("soc") or "Standart İşlemci"
    ).strip()

    gpu_name = str(
        raw.get("gpu_name") or raw.get("gpu") or raw.get("graphics") or
        raw.get("ekran_karti") or raw.get("vga") or "Tümleşik Grafik"
    ).strip()

    # 9. Hardware Scores (0 - 100)
    cpu_score_raw = raw.get("cpu_score")
    if cpu_score_raw is not None and str(cpu_score_raw).strip() not in ("", "null", "None"):
        try:
            cpu_score = max(0, min(100, int(float(str(cpu_score_raw)))))
        except Exception:
            cpu_score = estimate_cpu_score(cpu_name)
    else:
        cpu_score = estimate_cpu_score(cpu_name)

    gpu_score_raw = raw.get("gpu_score")
    if gpu_score_raw is not None and str(gpu_score_raw).strip() not in ("", "null", "None"):
        try:
            gpu_score = max(0, min(100, int(float(str(gpu_score_raw)))))
        except Exception:
            gpu_score = estimate_gpu_score(gpu_name)
    else:
        gpu_score = estimate_gpu_score(gpu_name)

    # Battery Score
    battery_score_raw = raw.get("battery_score") or raw.get("battery") or raw.get("pil") or raw.get("batarya")
    if battery_score_raw is not None and str(battery_score_raw).strip() not in ("", "null", "None"):
        try:
            b_str = str(battery_score_raw).lower()
            if "mah" in b_str:
                m = re.search(r"(\d+)", b_str)
                mah = int(m.group(1)) if m else 5000
                battery_score = 88 if mah >= 5000 else (84 if mah >= 4500 else 76)
            else:
                battery_score = max(0, min(100, int(float(b_str))))
        except Exception:
            battery_score = 85 if category in ("phone", "tablet") else 70
    else:
        battery_score = 85 if category in ("phone", "tablet") else 70

    # Display Score
    display_score_raw = raw.get("display_score") or raw.get("display") or raw.get("screen") or raw.get("ekran")
    if display_score_raw is not None and str(display_score_raw).strip() not in ("", "null", "None"):
        try:
            display_score = max(0, min(100, int(float(str(display_score_raw)))))
        except Exception:
            display_score = 90 if category in ("phone", "tablet") else 80
    else:
        display_score = 90 if category in ("phone", "tablet") else 80

    # Camera or Stylus Score
    camera_score_raw = (
        raw.get("camera_or_stylus_score") or raw.get("camera_score") or
        raw.get("stylus_score") or raw.get("camera") or raw.get("kamera") or raw.get("kalem")
    )
    if camera_score_raw is not None and str(camera_score_raw).strip() not in ("", "null", "None"):
        try:
            camera_or_stylus_score = max(0, min(100, int(float(str(camera_score_raw)))))
        except Exception:
            camera_or_stylus_score = 85 if category == "phone" else (88 if category == "tablet" else 65)
    else:
        camera_or_stylus_score = 85 if category == "phone" else (88 if category == "tablet" else 65)

    return {
        "category": category,
        "brand": brand,
        "model": model,
        "price_try": price_try,
        "ram_gb": ram_gb,
        "storage_gb": storage_gb,
        "weight_kg": weight_kg,
        "cpu_name": cpu_name,
        "gpu_name": gpu_name,
        "cpu_score": cpu_score,
        "gpu_score": gpu_score,
        "battery_score": battery_score,
        "display_score": display_score,
        "camera_or_stylus_score": camera_or_stylus_score
    }


def load_file(filepath: str) -> List[Dict[str, Any]]:
    """Loads records from JSON or CSV file."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Veri dosyası bulunamadı: {filepath}")

    ext = os.path.splitext(filepath)[1].lower()
    raw_records: List[Dict[str, Any]] = []

    if ext == ".json":
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                raw_records = data
            elif isinstance(data, dict) and "devices" in data:
                raw_records = data["devices"]
            else:
                raw_records = [data]
    elif ext in (".csv", ".txt"):
        with open(filepath, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            raw_records = [row for row in reader]
    else:
        raise ValueError(f"Desteklenmeyen dosya uzantısı: {ext}. Yalnızca .json veya .csv desteklenir.")

    return raw_records


def run_etl(
    source_file: Optional[str] = None,
    raw_data: Optional[List[Dict[str, Any]]] = None,
    db_path: Optional[str] = None,
    dry_run: bool = False
) -> Dict[str, Any]:
    """Runs ETL pipeline and returns statistics and cleaned items."""
    if not db_path:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        db_path = os.path.join(base_dir, "data", "devices.db")

    if source_file:
        records = load_file(source_file)
    elif raw_data is not None:
        records = raw_data
    else:
        raise ValueError("Lütfen source_file veya raw_data parametresi verin.")

    cleaned_records = [clean_and_normalize_record(r) for r in records]

    inserted_count = 0
    if not dry_run and cleaned_records:
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Ensure table exists
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS devices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL CHECK(category IN ('laptop', 'phone', 'tablet')),
            brand TEXT NOT NULL,
            model TEXT NOT NULL,
            price_try REAL NOT NULL,
            ram_gb INTEGER,
            storage_gb INTEGER NOT NULL,
            weight_kg REAL,
            cpu_name TEXT NOT NULL,
            gpu_name TEXT NOT NULL,
            cpu_score INTEGER NOT NULL CHECK(cpu_score BETWEEN 0 AND 100),
            gpu_score INTEGER NOT NULL CHECK(gpu_score BETWEEN 0 AND 100),
            battery_score INTEGER NOT NULL CHECK(battery_score BETWEEN 0 AND 100),
            display_score INTEGER NOT NULL CHECK(display_score BETWEEN 0 AND 100),
            camera_or_stylus_score INTEGER NOT NULL CHECK(camera_or_stylus_score BETWEEN 0 AND 100)
        );
        """)

        insert_sql = """
        INSERT INTO devices (
            category, brand, model, price_try, ram_gb, storage_gb,
            weight_kg, cpu_name, gpu_name, cpu_score, gpu_score,
            battery_score, display_score, camera_or_stylus_score
        ) VALUES (
            :category, :brand, :model, :price_try, :ram_gb, :storage_gb,
            :weight_kg, :cpu_name, :gpu_name, :cpu_score, :gpu_score,
            :battery_score, :display_score, :camera_or_stylus_score
        );
        """
        cursor.executemany(insert_sql, cleaned_records)
        conn.commit()
        inserted_count = len(cleaned_records)
        conn.close()

    return {
        "status": "success",
        "dry_run": dry_run,
        "processed_count": len(cleaned_records),
        "inserted_count": inserted_count,
        "db_path": db_path,
        "records": cleaned_records
    }


def main():
    parser = argparse.ArgumentParser(description="KDS Donanım ETL Veri İçe Aktarma Betiği")
    parser.add_argument("--file", "-f", required=True, help="İçe aktarılacak JSON veya CSV dosya yolu")
    parser.add_argument("--db", "-d", help="Hedef SQLite veritabanı yolu (varsayılan: data/devices.db)")
    parser.add_argument("--dry-run", action="store_true", help="Veritabanına yazmadan sadece temizlik ve skor hesaplamasını gösterir")

    args = parser.parse_args()
    print(f"[*] ETL Başlatılıyor: {args.file}")
    res = run_etl(source_file=args.file, db_path=args.db, dry_run=args.dry_run)
    print(f"[+] Başarılı! {res['processed_count']} cihaz temizlendi ve normalize edildi.")
    if args.dry_run:
        print("[!] Dry-run modunda çalıştı; veritabanına yazılmadı.")
    else:
        print(f"[+] {res['inserted_count']} kayıt '{res['db_path']}' veritabanına eklendi.")


if __name__ == "__main__":
    main()

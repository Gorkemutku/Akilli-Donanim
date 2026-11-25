"""
SQLite Database Access Layer & Seed Data for KDS Hardware Selection System.
"""
import os
import sqlite3
from typing import List, Dict, Any, Optional, Tuple

DEFAULT_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "devices.db")

SCHEMA_SQL = """
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
    camera_or_stylus_score INTEGER NOT NULL CHECK(camera_or_stylus_score BETWEEN 0 AND 100),
    last_synced_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_devices_category ON devices(category);
CREATE INDEX IF NOT EXISTS idx_devices_price ON devices(price_try);
CREATE UNIQUE INDEX IF NOT EXISTS idx_devices_brand_model ON devices(brand, model);

CREATE TABLE IF NOT EXISTS sync_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    synced_at TEXT NOT NULL,
    source TEXT NOT NULL,
    records_fetched INTEGER NOT NULL DEFAULT 0,
    records_inserted INTEGER NOT NULL DEFAULT 0,
    records_updated INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL CHECK(status IN ('SUCCESS', 'FAILED', 'WARNING')),
    error_message TEXT
);
CREATE INDEX IF NOT EXISTS idx_sync_logs_synced_at ON sync_logs(synced_at DESC);
"""

INITIAL_DEVICES: List[Dict[str, Any]] = [
    # --- LAPTOPS: OYUN (GAMING) ---
    {
        "category": "laptop",
        "brand": "Lenovo",
        "model": "Legion Pro 5 16IRX8",
        "price_try": 58500.0,
        "ram_gb": 32,
        "storage_gb": 1024,
        "weight_kg": 2.55,
        "cpu_name": "AMD Ryzen 7 7745HX",
        "gpu_name": "NVIDIA GeForce RTX 4070 (140W)",
        "cpu_score": 91,
        "gpu_score": 89,
        "battery_score": 62,
        "display_score": 90,
        "camera_or_stylus_score": 65
    },
    {
        "category": "laptop",
        "brand": "ASUS",
        "model": "ROG Strix G16 G614JV",
        "price_try": 46500.0,
        "ram_gb": 16,
        "storage_gb": 1024,
        "weight_kg": 2.50,
        "cpu_name": "Intel Core i7-13650HX",
        "gpu_name": "NVIDIA GeForce RTX 4060 (140W)",
        "cpu_score": 88,
        "gpu_score": 82,
        "battery_score": 60,
        "display_score": 86,
        "camera_or_stylus_score": 60
    },
    {
        "category": "laptop",
        "brand": "HP",
        "model": "OMEN 16-wf0029nt",
        "price_try": 64000.0,
        "ram_gb": 32,
        "storage_gb": 1024,
        "weight_kg": 2.39,
        "cpu_name": "Intel Core i7-14700HX",
        "gpu_name": "NVIDIA GeForce RTX 4070",
        "cpu_score": 94,
        "gpu_score": 89,
        "battery_score": 58,
        "display_score": 92,
        "camera_or_stylus_score": 65
    },
    {
        "category": "laptop",
        "brand": "MSI",
        "model": "Katana 15 B13VEK",
        "price_try": 38500.0,
        "ram_gb": 16,
        "storage_gb": 512,
        "weight_kg": 2.25,
        "cpu_name": "Intel Core i7-13620H",
        "gpu_name": "NVIDIA GeForce RTX 4050 (105W)",
        "cpu_score": 82,
        "gpu_score": 72,
        "battery_score": 55,
        "display_score": 75,
        "camera_or_stylus_score": 58
    },
    {
        "category": "laptop",
        "brand": "Acer",
        "model": "Nitro 16 AN16-41",
        "price_try": 33999.0,
        "ram_gb": 16,
        "storage_gb": 512,
        "weight_kg": 2.65,
        "cpu_name": "AMD Ryzen 5 7640HS",
        "gpu_name": "NVIDIA GeForce RTX 4050 (140W)",
        "cpu_score": 78,
        "gpu_score": 71,
        "battery_score": 66,
        "display_score": 81,
        "camera_or_stylus_score": 55
    },

    # --- LAPTOPS: HAFİF ULTRABOOK & İŞ (< 2.0 KG) ---
    {
        "category": "laptop",
        "brand": "Apple",
        "model": "MacBook Air 13 (M3)",
        "price_try": 51999.0,
        "ram_gb": 16,
        "storage_gb": 512,
        "weight_kg": 1.24,
        "cpu_name": "Apple M3 (8 çekirdek)",
        "gpu_name": "Apple M3 GPU (10 çekirdek)",
        "cpu_score": 86,
        "gpu_score": 62,
        "battery_score": 96,
        "display_score": 92,
        "camera_or_stylus_score": 85
    },
    {
        "category": "laptop",
        "brand": "Apple",
        "model": "MacBook Pro 14 (M3 Pro)",
        "price_try": 78999.0,
        "ram_gb": 18,
        "storage_gb": 512,
        "weight_kg": 1.61,
        "cpu_name": "Apple M3 Pro (12 çekirdek)",
        "gpu_name": "Apple M3 Pro GPU (18 çekirdek)",
        "cpu_score": 93,
        "gpu_score": 78,
        "battery_score": 94,
        "display_score": 98,
        "camera_or_stylus_score": 88
    },
    {
        "category": "laptop",
        "brand": "ASUS",
        "model": "Zenbook 14 OLED UX3405MA",
        "price_try": 44500.0,
        "ram_gb": 16,
        "storage_gb": 1024,
        "weight_kg": 1.20,
        "cpu_name": "Intel Core Ultra 7 155H",
        "gpu_name": "Intel Arc Graphics",
        "cpu_score": 84,
        "gpu_score": 55,
        "battery_score": 88,
        "display_score": 95,
        "camera_or_stylus_score": 80
    },
    {
        "category": "laptop",
        "brand": "Lenovo",
        "model": "ThinkPad T14s Gen 4",
        "price_try": 47900.0,
        "ram_gb": 16,
        "storage_gb": 512,
        "weight_kg": 1.25,
        "cpu_name": "AMD Ryzen 7 PRO 7840U",
        "gpu_name": "AMD Radeon 780M",
        "cpu_score": 85,
        "gpu_score": 56,
        "battery_score": 91,
        "display_score": 86,
        "camera_or_stylus_score": 78
    },
    {
        "category": "laptop",
        "brand": "Dell",
        "model": "XPS 13 Plus 9320",
        "price_try": 52500.0,
        "ram_gb": 16,
        "storage_gb": 512,
        "weight_kg": 1.26,
        "cpu_name": "Intel Core i7-1360P",
        "gpu_name": "Intel Iris Xe Graphics",
        "cpu_score": 80,
        "gpu_score": 48,
        "battery_score": 79,
        "display_score": 94,
        "camera_or_stylus_score": 76
    },
    {
        "category": "laptop",
        "brand": "LG",
        "model": "Gram 16 16Z90S",
        "price_try": 42000.0,
        "ram_gb": 16,
        "storage_gb": 512,
        "weight_kg": 1.19,
        "cpu_name": "Intel Core Ultra 5 125H",
        "gpu_name": "Intel Arc Graphics",
        "cpu_score": 81,
        "gpu_score": 52,
        "battery_score": 93,
        "display_score": 88,
        "camera_or_stylus_score": 75
    },

    # --- LAPTOPS: 8 GB RAM GİRİŞ SEVİYESİ / OFİS (Oyun Kısıtıyla Elenme Testi) ---
    {
        "category": "laptop",
        "brand": "Lenovo",
        "model": "IdeaPad 1 15AMN7",
        "price_try": 13999.0,
        "ram_gb": 8,
        "storage_gb": 256,
        "weight_kg": 1.58,
        "cpu_name": "AMD Ryzen 3 7320U",
        "gpu_name": "AMD Radeon 610M",
        "cpu_score": 48,
        "gpu_score": 28,
        "battery_score": 65,
        "display_score": 58,
        "camera_or_stylus_score": 50
    },
    {
        "category": "laptop",
        "brand": "HP",
        "model": "15s-fq5008nt",
        "price_try": 16500.0,
        "ram_gb": 8,
        "storage_gb": 512,
        "weight_kg": 1.69,
        "cpu_name": "Intel Core i5-1235U",
        "gpu_name": "Intel Iris Xe Graphics (80EU)",
        "cpu_score": 62,
        "gpu_score": 42,
        "battery_score": 68,
        "display_score": 64,
        "camera_or_stylus_score": 55
    },
    {
        "category": "laptop",
        "brand": "Acer",
        "model": "Aspire 3 A315-24P",
        "price_try": 15999.0,
        "ram_gb": 8,
        "storage_gb": 512,
        "weight_kg": 1.78,
        "cpu_name": "AMD Ryzen 5 7520U",
        "gpu_name": "AMD Radeon 610M",
        "cpu_score": 58,
        "gpu_score": 32,
        "battery_score": 70,
        "display_score": 62,
        "camera_or_stylus_score": 52
    },
    {
        "category": "laptop",
        "brand": "ASUS",
        "model": "Vivobook Go 15 E1504FA",
        "price_try": 16900.0,
        "ram_gb": 8,
        "storage_gb": 512,
        "weight_kg": 1.63,
        "cpu_name": "AMD Ryzen 5 7520U",
        "gpu_name": "AMD Radeon 610M",
        "cpu_score": 58,
        "gpu_score": 32,
        "battery_score": 68,
        "display_score": 65,
        "camera_or_stylus_score": 54
    },

    # --- PHONES (TELEFONLAR) ---
    {
        "category": "phone",
        "brand": "Apple",
        "model": "iPhone 15 Pro Max",
        "price_try": 76999.0,
        "ram_gb": 8,
        "storage_gb": 256,
        "weight_kg": 0.22,
        "cpu_name": "Apple A17 Pro",
        "gpu_name": "Apple 6-core GPU",
        "cpu_score": 96,
        "gpu_score": 94,
        "battery_score": 86,
        "display_score": 96,
        "camera_or_stylus_score": 97
    },
    {
        "category": "phone",
        "brand": "Samsung",
        "model": "Galaxy S24 Ultra",
        "price_try": 69999.0,
        "ram_gb": 12,
        "storage_gb": 256,
        "weight_kg": 0.23,
        "cpu_name": "Snapdragon 8 Gen 3 for Galaxy",
        "gpu_name": "Adreno 750",
        "cpu_score": 95,
        "gpu_score": 93,
        "battery_score": 88,
        "display_score": 97,
        "camera_or_stylus_score": 96
    },
    {
        "category": "phone",
        "brand": "Xiaomi",
        "model": "14 512GB",
        "price_try": 44999.0,
        "ram_gb": 12,
        "storage_gb": 512,
        "weight_kg": 0.19,
        "cpu_name": "Snapdragon 8 Gen 3",
        "gpu_name": "Adreno 750",
        "cpu_score": 93,
        "gpu_score": 90,
        "battery_score": 82,
        "display_score": 91,
        "camera_or_stylus_score": 89
    },
    {
        "category": "phone",
        "brand": "Google",
        "model": "Pixel 8 Pro",
        "price_try": 38500.0,
        "ram_gb": 12,
        "storage_gb": 128,
        "weight_kg": 0.21,
        "cpu_name": "Google Tensor G3",
        "gpu_name": "Immortalis-G715s MC10",
        "cpu_score": 84,
        "gpu_score": 78,
        "battery_score": 80,
        "display_score": 93,
        "camera_or_stylus_score": 95
    },
    {
        "category": "phone",
        "brand": "Samsung",
        "model": "Galaxy A55 5G",
        "price_try": 17500.0,
        "ram_gb": 8,
        "storage_gb": 128,
        "weight_kg": 0.21,
        "cpu_name": "Samsung Exynos 1480",
        "gpu_name": "Xclipse 530",
        "cpu_score": 68,
        "gpu_score": 62,
        "battery_score": 87,
        "display_score": 84,
        "camera_or_stylus_score": 74
    },
    {
        "category": "phone",
        "brand": "Xiaomi",
        "model": "Redmi Note 13 Pro+ 5G",
        "price_try": 20999.0,
        "ram_gb": 12,
        "storage_gb": 256,
        "weight_kg": 0.20,
        "cpu_name": "MediaTek Dimensity 7200 Ultra",
        "gpu_name": "Mali-G610 MC4",
        "cpu_score": 74,
        "gpu_score": 68,
        "battery_score": 85,
        "display_score": 86,
        "camera_or_stylus_score": 81
    },

    # --- TABLETS (TABLETLER) ---
    {
        "category": "tablet",
        "brand": "Apple",
        "model": "iPad Pro 11 (M4)",
        "price_try": 42999.0,
        "ram_gb": 8,
        "storage_gb": 256,
        "weight_kg": 0.44,
        "cpu_name": "Apple M4 (9 çekirdek)",
        "gpu_name": "Apple M4 GPU (10 çekirdek)",
        "cpu_score": 98,
        "gpu_score": 95,
        "battery_score": 88,
        "display_score": 98,
        "camera_or_stylus_score": 96
    },
    {
        "category": "tablet",
        "brand": "Apple",
        "model": "iPad Air 11 (M2)",
        "price_try": 26999.0,
        "ram_gb": 8,
        "storage_gb": 128,
        "weight_kg": 0.46,
        "cpu_name": "Apple M2 (8 çekirdek)",
        "gpu_name": "Apple M2 GPU (10 çekirdek)",
        "cpu_score": 89,
        "gpu_score": 84,
        "battery_score": 85,
        "display_score": 89,
        "camera_or_stylus_score": 88
    },
    {
        "category": "tablet",
        "brand": "Samsung",
        "model": "Galaxy Tab S9",
        "price_try": 24999.0,
        "ram_gb": 8,
        "storage_gb": 128,
        "weight_kg": 0.50,
        "cpu_name": "Snapdragon 8 Gen 2 for Galaxy",
        "gpu_name": "Adreno 740",
        "cpu_score": 88,
        "gpu_score": 86,
        "battery_score": 86,
        "display_score": 93,
        "camera_or_stylus_score": 92
    },
    {
        "category": "tablet",
        "brand": "Apple",
        "model": "iPad 10. Nesil",
        "price_try": 15999.0,
        "ram_gb": 4,
        "storage_gb": 64,
        "weight_kg": 0.48,
        "cpu_name": "Apple A14 Bionic",
        "gpu_name": "Apple 4-core GPU",
        "cpu_score": 72,
        "gpu_score": 68,
        "battery_score": 82,
        "display_score": 80,
        "camera_or_stylus_score": 75
    },
    {
        "category": "tablet",
        "brand": "Xiaomi",
        "model": "Pad 6",
        "price_try": 12999.0,
        "ram_gb": 8,
        "storage_gb": 128,
        "weight_kg": 0.49,
        "cpu_name": "Snapdragon 870",
        "gpu_name": "Adreno 650",
        "cpu_score": 76,
        "gpu_score": 72,
        "battery_score": 84,
        "display_score": 86,
        "camera_or_stylus_score": 76
    },
    {
        "category": "tablet",
        "brand": "Lenovo",
        "model": "Tab P12",
        "price_try": 11500.0,
        "ram_gb": 8,
        "storage_gb": 128,
        "weight_kg": 0.61,
        "cpu_name": "MediaTek Dimensity 7050",
        "gpu_name": "Mali-G68 MC4",
        "cpu_score": 66,
        "gpu_score": 60,
        "battery_score": 80,
        "display_score": 84,
        "camera_or_stylus_score": 73
    }
]


def get_db_connection(db_path: str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    """Returns a SQLite connection with Row factory configured."""
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: str = DEFAULT_DB_PATH, force_reset: bool = False) -> int:
    """
    Initializes the database schema and populates with seed data if empty or forced.
    Returns the count of devices in the database.
    """
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    if force_reset:
        cursor.execute("DROP TABLE IF EXISTS devices;")
        cursor.execute("DROP TABLE IF EXISTS sync_logs;")

    cursor.executescript(SCHEMA_SQL)
    conn.commit()

    # Migration check: Ensure last_synced_at exists in existing devices table
    cursor.execute("PRAGMA table_info(devices);")
    columns = [row["name"] for row in cursor.fetchall()]
    if "last_synced_at" not in columns:
        cursor.execute("ALTER TABLE devices ADD COLUMN last_synced_at TEXT DEFAULT NULL;")
        cursor.execute("UPDATE devices SET last_synced_at = datetime('now', 'localtime') WHERE last_synced_at IS NULL;")
        conn.commit()

    cursor.execute("SELECT COUNT(*) as count FROM devices;")
    count = cursor.fetchone()["count"]

    if count == 0:
        insert_query = """
        INSERT INTO devices (
            category, brand, model, price_try, ram_gb, storage_gb,
            weight_kg, cpu_name, gpu_name, cpu_score, gpu_score,
            battery_score, display_score, camera_or_stylus_score,
            last_synced_at
        ) VALUES (
            :category, :brand, :model, :price_try, :ram_gb, :storage_gb,
            :weight_kg, :cpu_name, :gpu_name, :cpu_score, :gpu_score,
            :battery_score, :display_score, :camera_or_stylus_score,
            datetime('now', 'localtime')
        );
        """
        cursor.executemany(insert_query, INITIAL_DEVICES)
        conn.commit()
        count = len(INITIAL_DEVICES)

    conn.close()
    return count


def fetch_all_devices(db_path: str = DEFAULT_DB_PATH, category: Optional[str] = None) -> List[Dict[str, Any]]:
    """Fetches all devices, optionally filtered by category."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    if category:
        cursor.execute("SELECT * FROM devices WHERE category = ? ORDER BY price_try ASC;", (category,))
    else:
        cursor.execute("SELECT * FROM devices ORDER BY category, price_try ASC;")
    rows = cursor.fetchall()
    devices = [dict(row) for row in rows]
    conn.close()
    return devices


def insert_device(device_data: Dict[str, Any], db_path: str = DEFAULT_DB_PATH) -> int:
    """Inserts a single device into the database and returns its new ID."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    insert_query = """
    INSERT INTO devices (
        category, brand, model, price_try, ram_gb, storage_gb,
        weight_kg, cpu_name, gpu_name, cpu_score, gpu_score,
        battery_score, display_score, camera_or_stylus_score,
        last_synced_at
    ) VALUES (
        :category, :brand, :model, :price_try, :ram_gb, :storage_gb,
        :weight_kg, :cpu_name, :gpu_name, :cpu_score, :gpu_score,
        :battery_score, :display_score, :camera_or_stylus_score,
        datetime('now', 'localtime')
    );
    """
    cursor.execute(insert_query, {
        "category": device_data["category"],
        "brand": device_data["brand"],
        "model": device_data["model"],
        "price_try": float(device_data["price_try"]),
        "ram_gb": int(device_data["ram_gb"]) if device_data.get("ram_gb") is not None else None,
        "storage_gb": int(device_data["storage_gb"]),
        "weight_kg": float(device_data["weight_kg"]) if device_data.get("weight_kg") is not None else None,
        "cpu_name": device_data["cpu_name"],
        "gpu_name": device_data["gpu_name"],
        "cpu_score": int(device_data["cpu_score"]),
        "gpu_score": int(device_data["gpu_score"]),
        "battery_score": int(device_data["battery_score"]),
        "display_score": int(device_data["display_score"]),
        "camera_or_stylus_score": int(device_data["camera_or_stylus_score"])
    })
    new_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return new_id


def upsert_device(device_data: Dict[str, Any], db_path: str = DEFAULT_DB_PATH) -> Tuple[int, str]:
    """
    UPSERT: If a device with the same (brand, model) exists, updates prices and scores;
    otherwise inserts a new device record.
    Returns (device_id, "updated" | "inserted").
    """
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    brand = device_data["brand"].strip()
    model = device_data["model"].strip()

    cursor.execute("SELECT id FROM devices WHERE LOWER(brand) = LOWER(?) AND LOWER(model) = LOWER(?);", (brand, model))
    existing = cursor.fetchone()

    if existing:
        device_id = existing["id"]
        update_query = """
        UPDATE devices SET
            category = :category,
            price_try = :price_try,
            ram_gb = :ram_gb,
            storage_gb = :storage_gb,
            weight_kg = :weight_kg,
            cpu_name = :cpu_name,
            gpu_name = :gpu_name,
            cpu_score = :cpu_score,
            gpu_score = :gpu_score,
            battery_score = :battery_score,
            display_score = :display_score,
            camera_or_stylus_score = :camera_or_stylus_score,
            last_synced_at = datetime('now', 'localtime')
        WHERE id = :id;
        """
        cursor.execute(update_query, {
            "id": device_id,
            "category": device_data["category"],
            "price_try": float(device_data["price_try"]),
            "ram_gb": int(device_data["ram_gb"]) if device_data.get("ram_gb") is not None else None,
            "storage_gb": int(device_data["storage_gb"]),
            "weight_kg": float(device_data["weight_kg"]) if device_data.get("weight_kg") is not None else None,
            "cpu_name": device_data["cpu_name"],
            "gpu_name": device_data["gpu_name"],
            "cpu_score": int(device_data["cpu_score"]),
            "gpu_score": int(device_data["gpu_score"]),
            "battery_score": int(device_data["battery_score"]),
            "display_score": int(device_data["display_score"]),
            "camera_or_stylus_score": int(device_data["camera_or_stylus_score"])
        })
        conn.commit()
        conn.close()
        return device_id, "updated"
    else:
        conn.close()
        new_id = insert_device(device_data, db_path)
        return new_id, "inserted"


def log_sync(
    source: str,
    records_fetched: int,
    records_inserted: int,
    records_updated: int,
    status: str,
    error_message: Optional[str] = None,
    db_path: str = DEFAULT_DB_PATH
) -> int:
    """Logs a daily/manual synchronization run into sync_logs table."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO sync_logs (
        synced_at, source, records_fetched, records_inserted,
        records_updated, status, error_message
    ) VALUES (
        datetime('now', 'localtime'), ?, ?, ?, ?, ?, ?
    );
    """, (source, records_fetched, records_inserted, records_updated, status, error_message))
    log_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return log_id


def get_last_sync_info(db_path: str = DEFAULT_DB_PATH) -> Optional[Dict[str, Any]]:
    """Returns the most recent sync log record, if any."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("""
    SELECT id, synced_at, source, records_fetched, records_inserted,
           records_updated, status, error_message
    FROM sync_logs
    ORDER BY synced_at DESC, id DESC
    LIMIT 1;
    """)
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_sync_history(limit: int = 10, db_path: str = DEFAULT_DB_PATH) -> List[Dict[str, Any]]:
    """Returns past synchronization logs."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("""
    SELECT id, synced_at, source, records_fetched, records_inserted,
           records_updated, status, error_message
    FROM sync_logs
    ORDER BY synced_at DESC, id DESC
    LIMIT ?;
    """, (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def delete_device(device_id: int, db_path: str = DEFAULT_DB_PATH) -> bool:
    """Deletes a device by its ID."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM devices WHERE id = ?;", (device_id,))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted

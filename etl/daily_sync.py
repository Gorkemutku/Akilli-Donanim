"""
Daily Live Data Synchronization and Normalization Script for KDS.
Fetches up-to-date hardware specs and pricing from external live feed/API,
cleans and normalizes records, and executes UPSERT into SQLite devices.db.
Logs execution statistics into sync_logs table.
"""
import os
import sys
import json
import logging
import argparse
import urllib.request
import urllib.error
from datetime import datetime
from typing import Dict, Any, List, Optional

# Ensure project root is in sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)


def load_dotenv_if_present(base_dir: str):
    """Loads environment variables from .env file at base_dir if present."""
    env_file = os.path.join(base_dir, ".env")
    if os.path.isfile(env_file):
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    k = k.strip()
                    v = v.strip().strip("'\"")
                    if k and k not in os.environ:
                        os.environ[k] = v


load_dotenv_if_present(BASE_DIR)

from kds.database import (
    DEFAULT_DB_PATH,
    init_db,
    upsert_device,
    log_sync,
    get_last_sync_info
)
from etl.import_devices import clean_and_normalize_record

# Configurable live endpoints
DEFAULT_LIVE_FEED_URL = os.environ.get(
    "LIVE_DEVICES_FEED_URL",
    "https://raw.githubusercontent.com/datasets/hardware-prices/master/devices.json"
)
BACKUP_FEED_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "live_feed_backup.json")

# Logger setup
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("KDS_DailySync")


def extract_records_from_json(data: Any) -> List[Dict[str, Any]]:
    """Extracts device records list from diverse JSON root payloads."""
    if isinstance(data, list):
        return data
    elif isinstance(data, dict):
        for key in ("devices", "data", "products", "items", "results", "records", "cihazlar"):
            if key in data and isinstance(data[key], list):
                return data[key]
        return [data]
    raise ValueError("JSON verisi bir liste veya geçerli cihaz nesnesi içermiyor.")


def fetch_from_remote_url(url: str, timeout: int = 5) -> List[Dict[str, Any]]:
    """Fetches JSON device records from a remote live endpoint or local file URL."""
    logger.info(f"Canlı veri kaynağına bağlanılıyor: {url}")

    # Handle local file paths passed as URL (e.g. file:///... or local relative/absolute path)
    if url.startswith("file://") or os.path.exists(url):
        clean_path = url.replace("file://", "")
        with open(clean_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return extract_records_from_json(data)

    req = urllib.request.Request(
        url,
        headers={"User-Agent": "KDS-Device-Sync-Bot/2.4 (Decision Support Systems Project)"}
    )
    with urllib.request.urlopen(req, timeout=timeout) as response:
        if response.status != 200:
            raise urllib.error.HTTPError(url, response.status, "Sunucu yanıt kodu geçersiz", response.headers, None)
        charset = response.info().get_content_charset() or "utf-8"
        content = response.read().decode(charset)
        data = json.loads(content)
        return extract_records_from_json(data)


def load_local_backup_feed(path: str = BACKUP_FEED_PATH) -> List[Dict[str, Any]]:
    """Loads local live backup feed when remote network is unreachable."""
    logger.info(f"Yerel yedek canlı veri beslemesi yükleniyor: {path}")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Yedek veri beslemesi bulunamadı: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def run_daily_sync(
    source_url: Optional[str] = None,
    db_path: str = DEFAULT_DB_PATH,
    force_backup: bool = False,
    dry_run: bool = False
) -> Dict[str, Any]:
    """
    Executes the daily live synchronization pipeline.
    1. Fetches from live endpoint or triggers graceful backup fallback.
    2. Cleans & normalizes fields (price, RAM, weight, CPU/GPU scores).
    3. Executes UPSERT into SQLite devices table.
    4. Logs sync event into sync_logs table.
    """
    target_url = source_url or DEFAULT_LIVE_FEED_URL
    raw_records: List[Dict[str, Any]] = []
    source_label = target_url
    status = "SUCCESS"
    error_detail = None

    # Step 1: Fetch live data with fallback
    if force_backup:
        source_label = f"YEREL YEDEK BESLEME ({os.path.basename(BACKUP_FEED_PATH)})"
        raw_records = load_local_backup_feed(BACKUP_FEED_PATH)
    else:
        try:
            raw_records = fetch_from_remote_url(target_url, timeout=4)
            source_label = f"UZAK CANLI API ({target_url})"
        except Exception as net_err:
            logger.warning(f"Uzak kaynağa erişilemedi ({type(net_err).__name__}: {net_err}). Güvenli yerel yedek beslemeye geçiliyor...")
            status = "WARNING"
            error_detail = f"Uzak erişim uyarısı: {str(net_err)} -> Güvenli yerel güncel besleme kullanıldı."
            source_label = f"YEREL YEDEK BESLEME (Ağ hatası sonrası fallback: {os.path.basename(BACKUP_FEED_PATH)})"
            try:
                raw_records = load_local_backup_feed(BACKUP_FEED_PATH)
            except Exception as backup_err:
                status = "FAILED"
                error_detail = f"Kritik hata: Hem uzak kaynak hem yerel yedek okunamadı: {str(backup_err)}"
                logger.error(error_detail)
                if not dry_run:
                    log_sync(
                        source=source_label,
                        records_fetched=0,
                        records_inserted=0,
                        records_updated=0,
                        status="FAILED",
                        error_message=error_detail,
                        db_path=db_path
                    )
                return {
                    "status": "failed",
                    "error": error_detail,
                    "records_fetched": 0,
                    "records_inserted": 0,
                    "records_updated": 0
                }

    # Step 2: Normalization & KDS Scoring
    logger.info(f"{len(raw_records)} ham cihaz kaydı normalize ediliyor...")
    cleaned_records = []
    for raw in raw_records:
        try:
            norm = clean_and_normalize_record(raw)
            cleaned_records.append(norm)
        except Exception as norm_err:
            logger.warning(f"Kayıt normalize edilemedi ({raw.get('model', 'Bilinmeyen')}): {norm_err}")

    # Step 3: UPSERT into SQLite devices table
    inserted_count = 0
    updated_count = 0

    if not dry_run:
        init_db(db_path)
        for record in cleaned_records:
            try:
                dev_id, op_type = upsert_device(record, db_path)
                if op_type == "updated":
                    updated_count += 1
                else:
                    inserted_count += 1
            except Exception as upsert_err:
                logger.error(f"UPSERT hatası ({record.get('model')}): {upsert_err}")

        # Step 4: Record log into sync_logs table
        log_sync(
            source=source_label,
            records_fetched=len(cleaned_records),
            records_inserted=inserted_count,
            records_updated=updated_count,
            status=status,
            error_message=error_detail,
            db_path=db_path
        )
    else:
        # Dry-run counts
        logger.info("[DRY-RUN] Veritabanı değiştirilmedi.")
        updated_count = len(cleaned_records)

    sync_result = {
        "status": status.lower(),
        "synced_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "source": source_label,
        "records_fetched": len(cleaned_records),
        "records_inserted": inserted_count,
        "records_updated": updated_count,
        "error_message": error_detail,
        "db_path": db_path,
        "dry_run": dry_run
    }

    logger.info(
        f"Senkronizasyon tamamlandı: {len(cleaned_records)} kayıt incelendi "
        f"({updated_count} güncellendi, {inserted_count} yeni eklendi). Durum: {status}"
    )
    return sync_result


def main():
    parser = argparse.ArgumentParser(description="KDS Günlük Canlı Veri Senkronizasyon Betiği")
    parser.add_argument("--source-url", "-u", help="Canlı veri kaynağı URL'si")
    parser.add_argument("--db", "-d", default=DEFAULT_DB_PATH, help="Hedef SQLite veritabanı yolu")
    parser.add_argument("--force-backup", "-b", action="store_true", help="Uzak bağlantıyı atlayıp doğrudan yerel canlı yedek feed'i kullanır")
    parser.add_argument("--dry-run", action="store_true", help="Veritabanına yazmadan sadece normalizasyon ve çekme sonucunu raporlar")

    args = parser.parse_args()
    res = run_daily_sync(
        source_url=args.source_url,
        db_path=args.db,
        force_backup=args.force_backup,
        dry_run=args.dry_run
    )
    print(json.dumps(res, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

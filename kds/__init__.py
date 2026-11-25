"""
KDS (Decision Support Systems) Core Package
"""
from .database import (
    init_db,
    get_db_connection,
    fetch_all_devices,
    insert_device,
    upsert_device,
    delete_device,
    log_sync,
    get_last_sync_info,
    get_sync_history,
    DEFAULT_DB_PATH
)
from .decision_engine import (
    evaluate_devices,
    synthesize_laptop_weights,
    build_google_search_link
)

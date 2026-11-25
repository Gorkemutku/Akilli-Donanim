#!/usr/bin/env bash
# macOS / Linux Günlük KDS Canlı Veri Senkronizasyonu Betiği (Cron İçin)
# Her gün saat 09:00'da çalışmak üzere tasarlanmıştır.

set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." >/dev/null 2>&1 && pwd )"
cd "$DIR"

mkdir -p "$DIR/logs"
LOG_FILE="$DIR/logs/daily_sync.log"

echo "==========================================================" >> "$LOG_FILE"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] KDS Günlük Canlı Veri Senkronizasyonu Başlatılıyor..." >> "$LOG_FILE"

# Sanal ortam kontrolü
if [ -d "$DIR/.venv" ]; then
    source "$DIR/.venv/bin/activate"
elif [ -d "$DIR/venv" ]; then
    source "$DIR/venv/bin/activate"
fi

# Senkronizasyon betiğini çalıştır ve logla
python3 "$DIR/etl/daily_sync.py" >> "$LOG_FILE" 2>&1

EXIT_CODE=$?
if [ $EXIT_CODE -eq 0 ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Senkronizasyon başarıyla tamamlandı." >> "$LOG_FILE"
else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] HATA: Senkronizasyon kod $EXIT_CODE ile bitti." >> "$LOG_FILE"
fi

exit $EXIT_CODE

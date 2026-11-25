#!/usr/bin/env bash
# macOS / Linux Cron Kurulum Yardımcısı
# Bu betik KDS günlük senkronizasyonunu her gün saat 09:00'da çalışacak şekilde crontab'a ekler.

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." >/dev/null 2>&1 && pwd )"
CRON_CMD="$DIR/scripts/cron_daily_sync.sh"
CRON_SCHEDULE="0 9 * * * $CRON_CMD"

chmod +x "$CRON_CMD"

echo "=========================================================="
echo "  KDS Günlük Canlı Veri Zamanlayıcı Kurulumu (Cron)"
echo "=========================================================="
echo "Hedef Komut: $CRON_CMD"
echo "Zamanlama  : Her gün saat 09:00 ($CRON_SCHEDULE)"
echo ""

# Mevcut crontab içinde var mı kontrol et
if crontab -l 2>/dev/null | grep -Fq "$CRON_CMD"; then
    echo "[!] Görev zaten crontab içerisinde mevcut."
else
    (crontab -l 2>/dev/null; echo "$CRON_SCHEDULE") | crontab -
    echo "[+] Başarılı! Günlük KDS senkronizasyon görevi crontab'a eklendi."
fi

echo ""
echo "Mevcut Crontab Kayıtlarınız:"
crontab -l 2>/dev/null | grep "$CRON_CMD" || true
echo "=========================================================="

#!/usr/bin/env bash
# Akıllı Donanım ve Cihaz Seçim Sistemi - KDS Web Uygulaması Başlatıcı

set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

echo "=========================================================="
echo "  Akıllı Donanım ve Cihaz Seçim Sistemi (KDS / DSS)"
echo "  Karar Destek Sistemleri Proje Uygulaması"
echo "=========================================================="

# Check if .venv exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
elif [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "[*] Sanal ortam (.venv) oluşturuluyor..."
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
fi

export PORT="${PORT:-5050}"

echo "[*] SQLite veritabanı kontrol ediliyor (data/devices.db)..."
python3 -c "from kds.database import init_db; count = init_db(); print(f'[+] SQLite veritabanı hazır! Toplam {count} cihaz kayıtlı.')"

echo "[*] KDS Web Uygulaması başlatılıyor..."
echo "[+] Tarayıcınızda açın: http://localhost:$PORT"
echo "=========================================================="

python3 app.py

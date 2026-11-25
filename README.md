# Akıllı Donanım ve Cihaz Seçim Sistemi (KDS / DSS)
**Karar Destek Sistemleri (Decision Support Systems) Dersi Dönem Projesi**

Bu proje; bütçe, donanım gereksinimleri, kullanım amaçları ve taşınabilirlik gibi çok boyutlu kriterleri analiz ederek son kullanıcılar ve kurumlar için en uygun bilgisayar, telefon veya tablet seçimini gerçekleştiren **Çok Kriterli Karar Verme (MCDM - Multi-Criteria Decision Making)** tabanlı tam kapsamlı bir Karar Destek Sistemidir.

Arayüz, klasik bir akademik araştırma monografı ve kütüphane estetiğinde; taş/krem zemin (`#F7F5F0`), koyu lacivert (`#14213D`) ve koyu bordo (`#7F1D1D`) paletiyle tasarlanmıştır.

---

## 1. Mimari ve Teknoloji Yığını

- **Backend / Karar Motoru:** Python 3 (Flask REST API + Modüler KDS Karar Motoru)
- **Veritabanı Katmanı:** Yerel SQLite (`data/devices.db`)
- **Veri Temizleme & Dönüşüm (ETL):** `etl/import_devices.py` (CPU/GPU adlarından benchmark puanı çıkaran regex & kural tabanlı ETL)
- **Karar Destek Modeli:** Ağırlıklı Toplam Modeli (**WSM - Weighted Sum Model**) + Sert Kısıt Budama (**Hard Constraint Pruning**) + Dinamik Ağırlık Birleştirme
- **Ön Yüz:** Klasik akademik araştırma raporu temalı semantik HTML5, modern CSS3 (`static/css/academic_theme.css`) ve saf JS (`static/js/app.js`)

---

## 2. Veritabanı Şeması (`devices` Tablosu)

SQLite veritabanı dosyası `data/devices.db` altında yer alır. İlk çalıştırmada veya `/api/reset` çağrıldığında otomatik oluşturulur ve 27 gerçekçi örnek cihazla doldurulur.

```sql
CREATE TABLE devices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT NOT NULL CHECK(category IN ('laptop', 'phone', 'tablet')),
    brand TEXT NOT NULL,
    model TEXT NOT NULL,
    price_try REAL NOT NULL,
    ram_gb INTEGER,                          -- Telefon ve tablet için NULL olabilir
    storage_gb INTEGER NOT NULL,
    weight_kg REAL,                          -- Eksikse NULL olabilir
    cpu_name TEXT NOT NULL,
    gpu_name TEXT NOT NULL,
    cpu_score INTEGER NOT NULL CHECK(cpu_score BETWEEN 0 AND 100),
    gpu_score INTEGER NOT NULL CHECK(gpu_score BETWEEN 0 AND 100),
    battery_score INTEGER NOT NULL CHECK(battery_score BETWEEN 0 AND 100),
    display_score INTEGER NOT NULL CHECK(display_score BETWEEN 0 AND 100),
    camera_or_stylus_score INTEGER NOT NULL CHECK(camera_or_stylus_score BETWEEN 0 AND 100)
);

CREATE INDEX idx_devices_category ON devices(category);
CREATE INDEX idx_devices_price ON devices(price_try);
```

### Örnek Cihaz Dağılımı (27 Kayıt):
1. **Oyun Laptopları (Gaming):** Lenovo Legion Pro 5, ASUS ROG Strix G16, HP OMEN 16, MSI Katana 15, Acer Nitro 16 (16-32 GB RAM, RTX 40 Serisi, GPU puanı ≥ 70).
2. **Hafif Ultrabook & İş Laptopları (< 2.0 kg):** Apple MacBook Air M3 (1.24 kg), MacBook Pro 14 M3 Pro (1.61 kg), ASUS Zenbook 14 OLED (1.20 kg), Lenovo ThinkPad T14s (1.25 kg), Dell XPS 13 Plus (1.26 kg), LG Gram 16 (1.19 kg).
3. **8 GB RAM'li Giriş Seviyesi Laptoplar (Oyun Kısıtı Eleme Testi İçin):** Lenovo IdeaPad 1, HP 15s, Acer Aspire 3, ASUS Vivobook Go 15.
4. **Akıllı Telefonlar:** Apple iPhone 15 Pro Max, Samsung Galaxy S24 Ultra, Xiaomi 14, Google Pixel 8 Pro, Samsung Galaxy A55, Redmi Note 13 Pro+.
5. **Tabletler:** Apple iPad Pro 11 M4, iPad Air 11 M2, Samsung Galaxy Tab S9, iPad 10. Nesil, Xiaomi Pad 6, Lenovo Tab P12.

---

## 3. KDS İş Kuralları ve Karar Motoru

Sistem aday cihazları dört kademeli bir KDS süzgecinden geçirir:

### A. Sert Kısıtlar (Hard Constraints)
Puanlama aşamasına dahi girmeden ihlal durumunda cihazı doğrudan gerekçesiyle eleyen kurallar:
1. **Oyun Kısıtı:** Kullanıcı *Oyun* seçtiğinde `ram_gb < 16` olan bilgisayarlar (örneğin 8 GB RAM'li giriş laptopları) anında elenir (`"RAM 8 GB; Oyun için en az 16 GB gereklidir"`). Ayrıca `gpu_score < 65` veya `storage_gb < 512` olan cihazlar elenir.
2. **Oyun + Yazılım Geliştirme Kesişimi:** İkisi birden seçildiğinde iki amacın kesişim barajı uygulanır:
   - `ram_gb >= 16`
   - `storage_gb >= 512`
   - `cpu_score >= 70` (Çok iş parçacıklı derleme ve emülasyon için)
   - `gpu_score >= 65`
3. **Taşınabilirlik Kısıtı (< 2.0 kg kuralı):**
   - 2.0 kg altı cihazlar *Hafif* kabul edilir.
   - Sadece `Hafif (< 2.0 kg)` seçilirse, 2.0 kg ve üzerindeki tüm cihazlar elenir (`"Ağırlık 2.55 kg; < 2.0 kg hafiflik kısıtını aşmaktadır"`).
   - Birden fazla ağırlık bandı seçilirse seçilen aralıklara uyanlar kabul edilir.
4. **Bütçe Kısıtı ve Toleransı:** Kullanıcının belirttiği bütçeyi ve seçilen tolerans oranını (+%0, +%5 veya +%10) aşan cihazlar elenir. Tolerans bandındaki cihazlar elenmez ancak bütçe aşım oranına göre kademeli puan kırılır.
5. **Eksik Veri Güvenliği:** `price_try`, `cpu_score` veya `gpu_score` gibi kritik alanları eksik olan kayıtlar yutulmaz; elenenler listesinde *"Eksik veri: ... veritabanında tanımsız"* gerekçesiyle şeffafça raporlanır.

### B. Dinamik Kriter Ağırlıklandırması
Kullanıcı birden fazla kullanım amacı seçtiğinde (örneğin Oyun + Yazılım), her iki profilin donanım öncelikleri toplanarak normalize edilir:

$$w_j = \left( \frac{\sum_{k \in P} w_{j,k}}{\sum_{i} \sum_{k \in P} w_{i,k}} \right) \cdot (1 - w_{\text{fiyat}})$$

### C. Çok Kriterli Puanlama (WSM)
Adayların kriter puanları ($v_{ij}$) ve ağırlıklar ($w_j$) çarpılarak 0-100 arasında **KDS Uygunluk İndeksi** hesaplanır:

$$S_i = \sum_{j=1}^{m} w_j \cdot v_{ij}$$

### D. %60 Uygunluk Barajı
- **Uygunluk puanı %60.0 ve üzerinde olan TÜM cihazlar** sonuç panelinde azalan sırada listelenir.
- **Puanı %60'ın altında kalan cihazlar** elenen cihazlar tablosuna aktarılır ve *"Uygunluk puanı %54.2 (%60 barajının altında kaldı)"* gerekçesi gösterilir.

### E. Karar Gerekçesi ve Google Arama Bağlantısı
- Tavsiye edilen her cihaz için güçlü yönlerini ve bütçe/kriter uyumunu açıklayan Türkçe bir KDS Karar Gerekçesi metni üretilir.
- Cihaz adını ve "fiyat" kelimesini arayan güvenli Google linki oluşturulur: `https://www.google.com/search?q={brand}+{model}+fiyat`.

---

## 4. REST API Uç Noktaları

| Metod | Uç Nokta | Açıklama |
|---|---|---|
| `GET` | `/api/info` | Sistem ve SQLite veritabanı istatistikleri |
| `GET` | `/api/devices` | Tüm cihazları listeler (Opsiyonel: `?category=laptop`) |
| `POST` | `/api/devices` | Yeni cihaz kaydeder (SQLite `devices` tablosuna yazar) |
| `DELETE`| `/api/devices/<id>` | Belirtilen ID'li cihazı SQLite'tan kalıcı olarak siler |
| `POST` | `/api/devices/import` | JSON veya CSV veri setini toplu içe aktarır |
| `POST` | `/api/reset` | Veritabanını 27 örnek cihazla fabrika ayarlarına sıfırlar |
| `POST` | `/api/evaluate` | KDS Karar Analizi motorunu çalıştırır ve sonuçları döner |
| `POST` | `/api/sync/live` | Dış canlı kaynaktan senkronizasyonu anında tetikler |
| `GET`  | `/api/sync/status` | Son senkronizasyon zamanı, geçmiş loglar ve takvim bilgisi |

---

## 5. Canlı Veri Senkronizasyonu & Günlük Zamanlayıcı (`etl/daily_sync.py`)

Sistem, sahte/statik veriler yerine canlı güncel verileri günde 1 kez otomatik çekmek ve işlemek üzere tasarlanmıştır:
- **Canlı Veri Çekme:** Dış API veya canlı JSON feed'e bağlanır (`LIVE_DEVICES_FEED_URL`). Ağ hatası, bağlantı kesintisi veya geçersiz yanıt durumunda mevcut veritabanını bozmadan güvenli yerel canlı beslemeye (`etl/live_feed_backup.json`) otomatik fallback yapar.
- **UPSERT Mantığı:** `devices` tablosunda `(brand, model)` ikilisi mevcutsa güncel fiyat ve donanım skorlarını günceller (`updated`); yeni bir model ise yeni kayıt açar (`inserted`).
- **Loglama & Zaman Damgası:** Her işlem `devices.last_synced_at` alanını günceller ve `sync_logs` tablosuna çalışma zamanı, kaynak, çekilen/güncellenen/eklenen sayıları ve durumunu (`SUCCESS`, `WARNING`, `FAILED`) yazar.

### A. Tek Seferlik Manuel Test:
```bash
# Veritabanına yazmadan sadece kuru çalıştırma (dry-run):
python3 etl/daily_sync.py --dry-run

# Canlı senkronizasyonu hemen çalıştırma ve SQLite'a işleme:
python3 etl/daily_sync.py

# Kendi özel canlı JSON API veya dosya kaynağınızla test etme:
python3 etl/daily_sync.py --source-url "https://api.example.com/v1/devices" --dry-run
python3 etl/daily_sync.py --source-url "https://api.example.com/v1/devices"
```

### B. Canlı URL Ortam Değişkeni Yapılandırması (`.env`):
Proje kökünde `.env.example` dosyasını `.env` olarak kopyalayıp canlı API adresinizi tanımlayabilirsiniz:
```bash
cp .env.example .env
# .env dosyasını düzenleyin:
# LIVE_DEVICES_FEED_URL=https://api.siteniz.com/devices.json
```

### C. Otomatik Zamanlayıcı (Günde 1 Kez 09:00):
1. **Dahili Uygulama Zamanlayıcısı:** Uygulama (`app.py`) çalıştığı sürece arka planda bir daemon thread her gün saat **09:00**'da senkronizasyonu otomatik tetikler.
2. **macOS / Linux Crontab Kurulumu:**
   ```bash
   ./scripts/setup_cron.sh
   ```
   *(Crontab'a `0 9 * * * .../scripts/cron_daily_sync.sh` kaydını otomatik ekler).*
3. **Windows Görev Zamanlayıcısı (Task Scheduler) Kurulumu:**
   ```powershell
   powershell -ExecutionPolicy Bypass -File .\scripts\setup_windows_scheduler.ps1
   ```
4. **Web Arayüzünden Tek Tıkla Güncelleme:**
   Arayüzün üst çubuğunda veya *§ 2.0 Veritabanı* ve *§ 3.0 Metodoloji* sekmelerindeki **"↻ Şimdi Canlı Güncelle"** butonuna basarak istediğiniz an manuel canlı senkronizasyon başlatabilirsiniz.

---

## 6. Python ETL Betiği (`etl/import_devices.py`)

Ham veya dış kaynaklı veri setlerini (JSON veya CSV) okur, metin içindeki fiyatları (örn. `"45.000,00 TL"`), RAM ve ağırlıkları normalize eder. Regex kuralları ile CPU ve GPU modellerini analiz edip 0-100 arası KDS kıyaslama puanlarına dönüştürerek doğrudan SQLite veritabanına aktarır.

```bash
# Sadece temizlik ve skor hesaplamasını test etmek için (dry-run):
python3 etl/import_devices.py --file etl/sample_raw_devices.json --dry-run

# Veritabanına kaydetmek için:
python3 etl/import_devices.py --file etl/sample_raw_devices.json --db data/devices.db
```

---

## 7. Kurulum ve Çalıştırma Adımları

### Adım 1: Proje Dizinine Girin
```bash
cd /Users/gorkemutkutatar/Akillidonanim
```

### Adım 2: Sanal Ortamı Aktif Edin ve Bağımlılıkları Yükleyin
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Adım 3: Testleri Çalıştırın
Tüm KDS kurallarının, donanım eleme mekanizmalarının ve REST API uçlarının doğruluğunu test etmek için:
```bash
python3 -m unittest discover tests
```
*(12 testin tamamı otomatik olarak çalışır ve kuralları doğrular)*

### Adım 4: Uygulamayı Başlatın
Hazırlanan tek tıkla başlatma betiğini kullanabilirsiniz:
```bash
./run.sh
```
Veya doğrudan Python ile:
```bash
python3 app.py
```

### Adım 5: Web Arayüzünü Açın
Tarayıcınızda şu adrese gidin:
```
http://localhost:5050
```

---

## 8. Kullanıcı Arayüzü Sekmeleri

1. **§ 1.0 Karar Analizi (Değerlendirme):**
   - Kategori seçimi (Bilgisayar, Telefon, Tablet).
   - Maksimum bütçe ve tolerans ayarı.
   - Kullanım amacı çoklu seçimi (Oyun, Yazılım Geliştirme, Grafik Tasarım, Günlük Kullanım).
   - Taşınabilirlik aralığı çoklu seçimi (Hafif < 2.0 kg, Orta 2.0-2.5 kg, Ağır > 2.5 kg).
   - Doğrudan karar destek analiz özeti, dinamik ağırlıklar, uygulanan sert kısıtlar, %60 barajını aşan cihazların sıralı listesi ve elenen cihazların detaylı gerekçe tablosu.
2. **§ 2.0 Veritabanı Kayıtları (SQLite):**
   - SQLite veritabanındaki tüm kayıtların canlı listesi, kategori filtreleri, anlık metin arama.
   - Yeni cihaz ekleme formu (modal).
   - Cihaz silme işlemi (`DELETE /api/devices/<id>`).
3. **§ 3.0 Veri İçe Aktar & KDS Metodolojisi:**
   - Matematiksel MCDM formülleri, WSM modeli ve karar kuralları dokümantasyonu.
   - JSON / CSV doğrudan veri yapıştırma ve içe aktarma aracı (`POST /api/devices/import`).
   - Tek tıkla fabrika ayarlarına sıfırlama düğmesi (`POST /api/reset`).
   - Bağımsız CLI ETL betiği kullanım rehberi.

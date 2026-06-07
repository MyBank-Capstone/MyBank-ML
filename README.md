# MyBank ML Service

Machine Learning service untuk personalisasi rekomendasi MyBank.

## Struktur Repo (ringkasan)

```
MyBank-ML/
├── app.py                    # Flask app & endpoint utama
├── docker-compose.yml        # MySQL service untuk development
├── requirements.txt
├── README.md
├── test_connection.py        # Skrip cepat untuk cek koneksi DB
├── scripts/
│   └── import_data.py        # Impor CSV ke database
├── data/                     # Dataset (CSV yang digunakan oleh import_data.py)
│   ├── Accounts_Final.csv
│   ├── Transactions_Final.csv
│   ├── Interactions_Final.csv
│   └── Merchants.csv
├── models/                   # Tempat menyimpan model terlatih (pickle)
└── src/                      # Kode sumber: clustering, recommender, dll.
    ├── clustering.py
    ├── recommender.py
    ├── explainability.py
    ├── database.py
    ├── recommendation_logger.py
    ├── recommendation_history.py
    └── dashboard.py
```

## Setup & Quickstart

1. Clone repository

```bash
git clone https://github.com/<org>/MyBank-ML.git
cd MyBank-ML
```

2. Buat virtual environment (opsional) dan install dependency

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

3. Jalankan MySQL untuk development (menggunakan `docker-compose.yml` yang ada)

```bash
docker-compose up -d
```

4. Verifikasi koneksi ke database

```bash
python test_connection.py
```

5. Import data CSV ke database

```bash
python scripts/import_data.py
```

File `scripts/import_data.py` membaca CSV dari folder `data/` dan menulis ke database seperti dikonfigurasi di `src/database.py`.

6. Jalankan API

```bash
python app.py
```

Server berjalan di `http://127.0.0.1:5000`.

## Endpoints

- `GET /` — Health check
- `GET /dashboard` — Statistik dashboard (lihat implementation di `src/dashboard.py`)
- `GET /recommendations/<user_id>` — Riwayat rekomendasi untuk `user_id`
- `POST /recommend` — Dapatkan rekomendasi untuk satu user

Contoh request `POST /recommend`:

```bash
curl -X POST http://127.0.0.1:5000/recommend \
  -H "Content-Type: application/json" \
  -d '{"user_id": 100001}'
```

Contoh response (disederhanakan):

```json
{
  "user_id": 100001,
  "nama": "User_1",
  "cluster": { "id": 5, "label": "...", "penjelasan": "..." },
  "rekomendasi": { "widget_1_cf_merchant": [], "widget_2_cf_channel": [], "widget_3_cbf_fitur": [], "widget_4_cbf_promo": [] }
}
```

## Catatan teknis

- Database connection string ada di `src/database.py` (default: `mysql+pymysql://root:root@localhost:3306/mybank`).
- Catalog fitur dan promo didefinisikan langsung di `src/recommender.py` sebagai `FEATURE_CATALOG` dan `PROMO_CATALOG` (bukan file CSV).
- Model clustering dan preprocessor (jika disimpan) seharusnya ditempatkan di folder `models/` dan dimuat oleh `src/clustering.py`.

## Data files

CSV yang digunakan (letakkan di folder `data/`):
- `Accounts_Final.csv`
- `Transactions_Final.csv`
- `Interactions_Final.csv`
- `Merchants.csv`

Pastikan header CSV sesuai dengan skema yang dibutuhkan oleh `scripts/import_data.py`.

## Troubleshooting

- Jika aplikasi tidak menemukan tabel saat membaca data, jalankan `python scripts/import_data.py` untuk mengisi tabel dari CSV.
- Jika koneksi DB gagal, jalankan `docker-compose ps` dan periksa `src/database.py` agar host/port sesuai.
- Untuk dependency issues, jalankan `pip install -r requirements.txt` pada virtualenv yang aktif.

## Testing

- Gunakan `python test_connection.py` untuk memastikan koneksi DB.
- Untuk unit testing, tambah test sesuai kebutuhan (mis. `pytest`).

## Development & Formatting

- Ikuti gaya Python (PEP8). Disarankan menggunakan `black` dan `isort` di workflow development.

## Deployment singkat

- Gunakan image container untuk aplikasi Flask dengan WSGI server (mis. `gunicorn`). Pastikan koneksi DB diatur melalui variabel lingkungan.

Contoh perintah WSGI:

```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```
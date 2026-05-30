# MyBank ML Service

Machine Learning service untuk personalisasi rekomendasi MyBank.

## Struktur Repo

```
mybank-ml/
├── app.py                  # Flask app & endpoint utama
├── requirements.txt
├── .gitignore
├── README.md
├── data/                   # Dataset (tidak di-commit ke GitHub)
│   ├── Accounts_Final.csv
│   ├── Transactions_Final.csv
│   ├── Interactions_Final.csv
│   ├── feature_catalog.csv
│   └── promo_catalog.csv
├── models/                 # Trained model
│   ├── kmeans_model.pkl
│   └── preprocessor.pkl
└── src/
    ├── clustering.py       # Load model, predict cluster, auto labeling
    ├── recommender.py      # CF & CBF engine
    └── explainability.py   # XAI & explain cluster
```

## Setup

```bash
# 1. Clone repo
git clone https://github.com/<org>/mybank-ml.git
cd mybank-ml

# 2. Install dependencies
pip install -r requirements.txt

# 3. Pastikan folder data/ sudah berisi CSV dan folder models/ berisi .pkl

# 4. Jalankan
python app.py
```

## Endpoint

### `GET /`
Health check.

**Response:**
```json
{
  "status": "ok",
  "message": "MyBank ML API is running"
}
```

---

### `POST /recommend`
Rekomendasi hybrid (4 widget) untuk satu user.

**Request:**
```json
{
  "user_id": 100001
}
```

**Response:**
```json
{
  "user_id": 100001,
  "nama": "User_1",
  "cluster": {
    "id": 5,
    "label": "Freelancer Senior Menikah (Saving)",
    "penjelasan": "Masuk 'Freelancer Senior Menikah (Saving)' karena: usia senior (≥ 55 tahun), pendapatan tinggi (≥ 10 juta), pekerjaan Freelancer, sudah menikah"
  },
  "rekomendasi": {
    "widget_1_cf_merchant": [
      { "merchant_name": "GrabFood", "penjelasan_xai": "..." }
    ],
    "widget_2_cf_channel": [
      { "channel": "QRIS", "penjelasan_xai": "..." }
    ],
    "widget_3_cbf_fitur": [
      { "feature": "Bayar Listrik (PLN)", "penjelasan_xai": "..." }
    ],
    "widget_4_cbf_promo": [
      { "merchant": "Starbucks", "penjelasan_xai": "..." }
    ]
  }
}
```

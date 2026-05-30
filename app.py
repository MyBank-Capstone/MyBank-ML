from flask import Flask, request, jsonify
import pandas as pd
import pickle
from datetime import datetime
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder

from src.clustering import load_model, prepare_features, get_cluster_labels
from src.recommender import get_cf_recommendation, cbf_engine, FEATURE_CATALOG, PROMO_CATALOG
from src.explainability import explain_cluster, apply_xai

app = Flask(__name__)

# ==========================================
# LOAD DATA & MODEL SAAT APP START
# ==========================================
df_account = pd.read_csv("data/Accounts_Final.csv")
df_trx = pd.read_csv("data/Transactions_Final.csv")
df_merchant = pd.read_csv("data/Merchants.csv")

# Merge merchant_name ke df_trx
df_trx = df_trx.merge(df_merchant[['merchant_id', 'merchant_name']], on='merchant_id', how='left')

model, preprocessor = load_model()

# Prepare df_account
df_account = prepare_features(df_account)

X = preprocessor.transform(df_account[['age', 'pekerjaan', 'income_encoded', 'status_pernikahan', 'account_type']])
df_account['cluster'] = model.predict(X)
cluster_labels = get_cluster_labels(df_account)
df_account['cluster_label'] = df_account['cluster'].map(cluster_labels)

# Merge cluster ke transaksi
df_trx_merged = df_trx.merge(df_account[['no_rek', 'cluster']], on='no_rek', how='left')

# Top merchants per cluster (untuk fallback CF)
top_merchants = (
    df_trx_merged[df_trx_merged['status'] == 'sukses']
    .groupby(['cluster', 'merchant_name'])
    .size()
    .reset_index(name='total_transaksi')
    .sort_values(['cluster', 'total_transaksi'], ascending=[True, False])
    .groupby('cluster')
    .head(3)
)


# ==========================================
# ENDPOINT: HEALTH CHECK
# ==========================================
@app.route("/", methods=["GET"])
def health_check():
    return jsonify({"status": "ok", "message": "MyBank ML API is running"})


# ==========================================
# ENDPOINT: REKOMENDASI HYBRID
# ==========================================
@app.route("/recommend", methods=["POST"])
def recommend():
    data = request.get_json()
    user_id = data.get("user_id")

    if not user_id:
        return jsonify({"error": "user_id is required"}), 400

    user_id = int(user_id)

    if user_id not in df_account['no_rek'].values:
        return jsonify({"error": f"User {user_id} tidak ditemukan"}), 404

    user_row = df_account[df_account['no_rek'] == user_id].iloc[0]
    cluster_id = int(user_row['cluster'])
    cluster_label = cluster_labels.get(cluster_id, f"Cluster {cluster_id}")
    cluster_explanation = explain_cluster(user_row, cluster_labels)

    # WIDGET 1: CF Merchant
    hasil_cf_merchant = get_cf_recommendation(
        target_user=user_id,
        df_trx=df_trx_merged,
        fallback_df=top_merchants,
        item_col='merchant_name',
        top_n=3
    )
    xai_cf_merchant = apply_xai(hasil_cf_merchant, tipe_model='CF')

    # WIDGET 2: CF Channel
    hasil_cf_channel = get_cf_recommendation(
        target_user=user_id,
        df_trx=df_trx_merged,
        fallback_df=None,
        item_col='channel',
        top_n=3
    )
    xai_cf_channel = apply_xai(hasil_cf_channel, tipe_model='CF')

    # WIDGET 3: CBF Fitur
    hasil_cbf_fitur = cbf_engine(
        user_id=user_id,
        df_trx=df_trx,
        catalog=FEATURE_CATALOG,
        item_name='feature',
        channel_weight=0.6,
        kategori_weight=0.4,
        top_n=3
    )
    xai_cbf_fitur = apply_xai(hasil_cbf_fitur, tipe_model='CBF')

    # WIDGET 4: CBF Promo
    hasil_cbf_promo = cbf_engine(
        user_id=user_id,
        df_trx=df_trx,
        catalog=PROMO_CATALOG,
        item_name='merchant',
        channel_weight=0.3,
        kategori_weight=0.7,
        top_n=3
    )
    xai_cbf_promo = apply_xai(hasil_cbf_promo, tipe_model='CBF')

    # FORMAT RESPONSE
    response = {
        "user_id": user_id,
        "nama": user_row['nama'],
        "cluster": {
            "id": cluster_id,
            "label": cluster_label,
            "penjelasan": cluster_explanation
        },
        "rekomendasi": {
            "widget_1_cf_merchant": xai_cf_merchant[['merchant_name', 'penjelasan_xai']].to_dict(orient='records') if not xai_cf_merchant.empty else [],
            "widget_2_cf_channel": xai_cf_channel[['channel', 'penjelasan_xai']].to_dict(orient='records') if not xai_cf_channel.empty else [],
            "widget_3_cbf_fitur": xai_cbf_fitur[['feature', 'penjelasan_xai']].to_dict(orient='records') if not xai_cbf_fitur.empty else [],
            "widget_4_cbf_promo": xai_cbf_promo[['merchant', 'penjelasan_xai']].to_dict(orient='records') if not xai_cbf_promo.empty else [],
        }
    }

    return jsonify(response)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
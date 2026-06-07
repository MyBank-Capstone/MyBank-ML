from flask import Flask, request, jsonify
import pandas as pd

from src.clustering import (
    load_model,
    prepare_features,
    get_cluster_labels
)

from src.recommender import (
    get_cf_recommendation,
    cbf_engine,
    FEATURE_CATALOG,
    PROMO_CATALOG
)

from src.explainability import (
    explain_cluster,
    apply_xai
)

from src.database import engine
from src.recommendation_logger import save_recommendation
from src.dashboard import get_dashboard_stats
from src.recommendation_history import get_recommendation_history

app = Flask(__name__)

# ==========================================
# LOAD DATA & MODEL SAAT APP START
# ==========================================

# Load clustering model
model, preprocessor = load_model()

def load_fresh_data():
    df_account = pd.read_sql(
        """
        SELECT 
            a.account_number AS no_rek, 
            a.account_type, 
            u.id AS user_id, 
            u.name AS nama, 
            u.date_of_birth AS tanggal_lahir, 
            u.occupation AS pekerjaan, 
            u.monthly_income_range, 
            u.marital_status AS status_pernikahan
        FROM accounts a
        JOIN users u ON a.user_id = u.id
        """,
        engine
    )

    df_trx = pd.read_sql(
        """
        SELECT 
            a.account_number AS no_rek,
            CASE WHEN t.status = 'SUCCESS' THEN 'sukses' ELSE LOWER(t.status) END AS status,
            t.merchant_name,
            t.merchant_category AS kategori,
            LOWER(t.type) AS channel
        FROM transactions t
        JOIN accounts a ON t.account_id = a.id
        """,
        engine
    )

    # Prepare account features
    df_account = prepare_features(df_account)

    X = preprocessor.transform(
        df_account[
            [
                "age",
                "pekerjaan",
                "income_encoded",
                "status_pernikahan",
                "account_type"
            ]
        ]
    )

    df_account["cluster"] = model.predict(X)

    cluster_labels = get_cluster_labels(df_account)

    df_account["cluster_label"] = (
        df_account["cluster"].map(cluster_labels)
    )

    # Merge cluster ke transaksi
    df_trx_merged = df_trx.merge(
        df_account[["no_rek", "cluster"]],
        on="no_rek",
        how="left"
    )

    # Top merchant per cluster (fallback CF)
    top_merchants = (
        df_trx_merged[df_trx_merged["status"] == "sukses"]
        .groupby(["cluster", "merchant_name"])
        .size()
        .reset_index(name="total_transaksi")
        .sort_values(
            ["cluster", "total_transaksi"],
            ascending=[True, False]
        )
        .groupby("cluster")
        .head(3)
    )
    
    return df_account, df_trx, df_trx_merged, top_merchants, cluster_labels

# ==========================================
# HELPER FUNCTION
# ==========================================

def log_recommendations(
    df,
    user_id,
    recommendation_type,
    item_column
):
    if df is None or df.empty:
        return

    for _, row in df.iterrows():
        save_recommendation(
            user_id=user_id,
            recommendation_type=recommendation_type,
            recommendation_item=row[item_column],
            score=row["score"],
            explanation=row["penjelasan_xai"]
        )

# ==========================================
# HEALTH CHECK
# ==========================================

@app.route("/", methods=["GET"])
def health_check():
    return jsonify({
        "status": "ok",
        "message": "MyBank ML API is running"
    })

@app.route("/dashboard", methods=["GET"])
def dashboard():

    stats = get_dashboard_stats()

    return jsonify(stats)

@app.route("/recommendations/<int:user_id>", methods=["GET"])
def recommendation_history(user_id):

    history = get_recommendation_history(user_id)

    return jsonify({
        "user_id": user_id,
        "total": len(history),
        "history": history
    })

# ==========================================
# RECOMMENDATION ENDPOINT
# ==========================================

@app.route("/recommend", methods=["POST"])
def recommend():

    data = request.get_json()

    user_id = data.get("user_id")

    if not user_id:
        return jsonify({
            "error": "user_id is required"
        }), 400

    user_id = int(user_id)

    # Load fresh data dari database setiap kali ada request
    df_account, df_trx, df_trx_merged, top_merchants, cluster_labels = load_fresh_data()

    if user_id not in df_account["user_id"].values:
        return jsonify({
            "error": f"User {user_id} tidak ditemukan"
        }), 404

    user_row = (
        df_account[df_account["user_id"] == user_id]
        .iloc[0]
    )

    no_rek = user_row["no_rek"]

    cluster_id = int(user_row["cluster"])

    cluster_label = cluster_labels.get(
        cluster_id,
        f"Cluster {cluster_id}"
    )

    cluster_explanation = explain_cluster(
        user_row,
        cluster_labels
    )

    # ======================================
    # WIDGET 1 - CF MERCHANT
    # ======================================

    hasil_cf_merchant = get_cf_recommendation(
        target_user=no_rek,
        df_trx=df_trx_merged,
        fallback_df=top_merchants,
        item_col="merchant_name",
        top_n=3
    )

    xai_cf_merchant = apply_xai(
        hasil_cf_merchant,
        tipe_model="CF"
    )

    # ======================================
    # WIDGET 2 - CF CHANNEL
    # ======================================

    hasil_cf_channel = get_cf_recommendation(
        target_user=no_rek,
        df_trx=df_trx_merged,
        fallback_df=None,
        item_col="channel",
        top_n=3
    )

    xai_cf_channel = apply_xai(
        hasil_cf_channel,
        tipe_model="CF"
    )

    # ======================================
    # WIDGET 3 - CBF FEATURE
    # ======================================

    hasil_cbf_fitur = cbf_engine(
        user_id=no_rek,
        df_trx=df_trx,
        catalog=FEATURE_CATALOG,
        item_name="feature",
        channel_weight=0.6,
        kategori_weight=0.4,
        top_n=3
    )

    xai_cbf_fitur = apply_xai(
        hasil_cbf_fitur,
        tipe_model="CBF"
    )

    # ======================================
    # WIDGET 4 - CBF PROMO
    # ======================================

    hasil_cbf_promo = cbf_engine(
        user_id=no_rek,
        df_trx=df_trx,
        catalog=PROMO_CATALOG,
        item_name="merchant",
        channel_weight=0.3,
        kategori_weight=0.7,
        top_n=3
    )

    xai_cbf_promo = apply_xai(
        hasil_cbf_promo,
        tipe_model="CBF"
    )

    # ======================================
    # SAVE RECOMMENDATIONS
    # ======================================

    log_recommendations(
        xai_cf_merchant,
        user_id,
        "CF_MERCHANT",
        "merchant_name"
    )

    log_recommendations(
        xai_cf_channel,
        user_id,
        "CF_CHANNEL",
        "channel"
    )

    log_recommendations(
        xai_cbf_fitur,
        user_id,
        "CBF_FEATURE",
        "feature"
    )

    log_recommendations(
        xai_cbf_promo,
        user_id,
        "CBF_PROMO",
        "merchant"
    )

    # ======================================
    # RESPONSE
    # ======================================

    response = {
        "user_id": user_id,
        "nama": user_row["nama"],
        "cluster": {
            "id": cluster_id,
            "label": cluster_label,
            "penjelasan": cluster_explanation
        },
        "rekomendasi": {
            "widget_1_cf_merchant": (
                xai_cf_merchant[
                    ["merchant_name", "penjelasan_xai"]
                ].to_dict(orient="records")
                if not xai_cf_merchant.empty
                else []
            ),
            "widget_2_cf_channel": (
                xai_cf_channel[
                    ["channel", "penjelasan_xai"]
                ].to_dict(orient="records")
                if not xai_cf_channel.empty
                else []
            ),
            "widget_3_cbf_fitur": (
                xai_cbf_fitur[
                    ["feature", "penjelasan_xai"]
                ].to_dict(orient="records")
                if not xai_cbf_fitur.empty
                else []
            ),
            "widget_4_cbf_promo": (
                xai_cbf_promo[
                    ["merchant", "penjelasan_xai"]
                ].to_dict(orient="records")
                if not xai_cbf_promo.empty
                else []
            )
        }
    }

    return jsonify(response)

# ==========================================
# RUN APP
# ==========================================

if __name__ == "__main__":
    app.run(
        debug=True,
        port=5000
    )
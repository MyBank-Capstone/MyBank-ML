import re
import pandas as pd


def explain_cluster(user_row, cluster_labels):
    cluster_id = user_row['cluster']
    label = cluster_labels.get(cluster_id, f"Cluster {cluster_id}")
    reasons = []

    if user_row['age'] >= 55:
        reasons.append("usia senior (≥ 55 tahun)")
    elif user_row['age'] <= 30:
        reasons.append(f"usia muda (≤ 30 tahun)")
    else:
        reasons.append(f"usia {int(user_row['age'])} tahun")

    if user_row['income_encoded'] <= 1:
        reasons.append("pendapatan rendah (< 5 juta)")
    elif user_row['income_encoded'] >= 3:
        reasons.append("pendapatan tinggi (≥ 10 juta)")
    else:
        reasons.append("pendapatan menengah")

    reasons.append(f"pekerjaan {user_row['pekerjaan']}")

    if user_row['status_pernikahan'] == 'single':
        reasons.append("belum menikah")
    else:
        reasons.append("sudah menikah")

    return f"Masuk '{label}' karena: {', '.join(reasons)}"


def generate_xai_text(row, tipe_model, konteks_tambahan=None):
    if 'merchant_name' in row:
        item_name = row['merchant_name']
    elif 'merchant' in row:
        item_name = row['merchant']
    elif 'channel' in row:
        item_name = row['channel']
    elif 'feature' in row:
        item_name = row['feature']
    else:
        item_name = "Layanan ini"

    if tipe_model == 'CF':
        return f"Kami merekomendasikan {item_name} karena disukai oleh nasabah lain yang gaya transaksinya mirip denganmu."

    elif tipe_model == 'CBF':
        alasan_raw = str(row.get('explanation', ''))
        matches = re.findall(r"\('([^']+)'", alasan_raw)

        reasons = []
        seen = set()

        for m in matches[:3]:
            if "channel_" in m:
                label = "layanan " + m.replace("channel_", "").replace("_", " ")
            elif "kategori_" in m:
                label = "kategori " + m.replace("kategori_", "").replace("_", " ")
            else:
                continue

            if label not in seen:
                seen.add(label)
                reasons.append(label)

        if reasons:
            if len(reasons) == 1:
                return f"Sesuai untukmu karena kamu aktif di {reasons[0]}."
            else:
                return f"Sesuai untukmu karena aktif di {reasons[0]} dan {reasons[1]}."
        else:
            return "Sesuai dengan riwayat transaksimu sebelumnya."

    elif tipe_model == 'CLUSTER_FALLBACK':
        nama_cluster = konteks_tambahan if konteks_tambahan else "kelompokmu"
        return f"{item_name} sedang banyak digunakan oleh nasabah di {nama_cluster}."

    return "Direkomendasikan khusus untukmu."


def apply_xai(df_rekomendasi, tipe_model, konteks_tambahan=None):
    if df_rekomendasi is None or df_rekomendasi.empty:
        return pd.DataFrame()

    df_hasil = df_rekomendasi.copy()
    df_hasil['penjelasan_xai'] = df_hasil.apply(
        lambda row: generate_xai_text(row, tipe_model, konteks_tambahan),
        axis=1
    )
    return df_hasil

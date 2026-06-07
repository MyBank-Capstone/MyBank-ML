import pickle
import pandas as pd
from datetime import datetime


def load_model(model_path="models/kmeans_model.pkl", preprocessor_path="models/preprocessor.pkl"):
    with open(model_path, "rb") as f:
        model = pickle.load(f)
    with open(preprocessor_path, "rb") as f:
        preprocessor = pickle.load(f)
    return model, preprocessor


def prepare_features(df_account):
    df = df_account.copy()
    df['tanggal_lahir'] = pd.to_datetime(df['tanggal_lahir'], errors='coerce')
    df['age'] = datetime.now().year - df['tanggal_lahir'].dt.year

    # Misal di db kolom age masil null, fill ini dulu aman kan? soalnya request data ini masih optional di be ku
    df['age'] = df['age'].fillna(30)

    income_mapping = {'<5 juta': 1, '5-10 juta': 2, '10-20 juta': 3, '>20 juta': 4}
    df['income_encoded'] = df['monthly_income_range'].map(income_mapping)

    # Ini juga fill dulu kalau masil null
    df['income_encoded'] = df['income_encoded'].fillna(1)
    if 'pekerjaan' in df.columns:
        df['pekerjaan'] = df['pekerjaan'].fillna('Lainnya')
    if 'status_pernikahan' in df.columns:
        df['status_pernikahan'] = df['status_pernikahan'].fillna('single')

    return df


def generate_cluster_label(row):
    parts = []
    parts.append(row['pekerjaan'])

    if row['age'] >= 55:
        parts.append("Senior")
    elif row['age'] <= 30:
        parts.append("Muda")
    else:
        parts.append("Menengah")

    if row['status_pernikahan'] == 'single':
        parts.append("Single")
    else:
        parts.append("Menikah")

    parts.append(f"({row['account_type']})")
    return " ".join(parts)


def get_cluster_labels(df_account):
    numeric_features = ['age', 'income_encoded']
    categorical_features = ['pekerjaan', 'status_pernikahan', 'account_type']

    cluster_profile = df_account.groupby('cluster').agg({
        'age': 'mean',
        'income_encoded': 'mean',
        'pekerjaan': lambda x: x.value_counts().index[0],
        'status_pernikahan': lambda x: x.value_counts().index[0],
        'account_type': lambda x: x.value_counts().index[0],
    })

    cluster_labels = {
        row.name: generate_cluster_label(row)
        for _, row in cluster_profile.iterrows()
    }
    return cluster_labels


def predict_cluster(user_data: dict, model, preprocessor):
    """
    Predict cluster untuk user baru.
    user_data: dict dengan keys no_rek, tanggal_lahir, pekerjaan,
               monthly_income_range, status_pernikahan, account_type
    """
    df = pd.DataFrame([user_data])
    df = prepare_features(df)

    features = df[['age', 'pekerjaan', 'income_encoded', 'status_pernikahan', 'account_type']]
    X = preprocessor.transform(features)
    cluster = model.predict(X)[0]
    return int(cluster)

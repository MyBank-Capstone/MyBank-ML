import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import OneHotEncoder


# ==========================================
# CATALOGS
# ==========================================
FEATURE_CATALOG = pd.DataFrame([
    # CORE
    {'feature': 'Pembayaran QRIS',          'channel': 'QRIS',            'kategori': None},
    {'feature': 'Transfer Uang',            'channel': 'transfer',        'kategori': None},
    # TAGIHAN
    {'feature': 'Bayar Listrik (PLN)',       'channel': 'mobile',          'kategori': 'Utilities'},
    {'feature': 'Bayar Air (PDAM)',          'channel': 'mobile',          'kategori': 'Utilities'},
    {'feature': 'Beli Pulsa/Data',           'channel': 'mobile',          'kategori': 'Utilities'},
    {'feature': 'Bayar Tagihan',             'channel': 'mobile',          'kategori': 'Utilities'},
    # E-COMMERCE
    {'feature': 'Top Up E-Wallet',           'channel': 'transfer',        'kategori': 'E-commerce'},
    {'feature': 'Pembayaran Marketplace',    'channel': 'virtual_account', 'kategori': 'E-commerce'},
    # LANGGANAN
    {'feature': 'Auto Debit Langganan',      'channel': 'transfer',        'kategori': 'Entertainment'},
    # ADVANCED
    {'feature': 'Transfer Terjadwal',        'channel': 'transfer',        'kategori': None},
    {'feature': 'Permintaan Uang',           'channel': 'transfer',        'kategori': None},
    {'feature': 'Transfer Favorit',          'channel': 'transfer',        'kategori': None},
])

PROMO_CATALOG = pd.DataFrame([
    {'merchant': 'Tokopedia',       'channel': 'virtual_account', 'kategori': 'E-commerce'},
    {'merchant': 'Shopee',          'channel': 'virtual_account', 'kategori': 'E-commerce'},
    {'merchant': 'Blibli',          'channel': 'virtual_account', 'kategori': 'E-commerce'},
    {'merchant': 'Starbucks',       'channel': 'QRIS',            'kategori': 'F&B'},
    {'merchant': 'McDonalds',       'channel': 'QRIS',            'kategori': 'F&B'},
    {'merchant': 'Kopi Kenangan',   'channel': 'QRIS',            'kategori': 'F&B'},
    {'merchant': 'Netflix',         'channel': 'transfer',        'kategori': 'Entertainment'},
    {'merchant': 'Spotify',         'channel': 'transfer',        'kategori': 'Entertainment'},
    {'merchant': 'Traveloka',       'channel': 'transfer',        'kategori': 'Travel'},
    {'merchant': 'Tiket.com',       'channel': 'virtual_account', 'kategori': 'Travel'},
    {'merchant': 'PLN',             'channel': 'mobile',          'kategori': 'Utilities'},
    {'merchant': 'Telkomsel',       'channel': 'mobile',          'kategori': 'Utilities'},
])


# ==========================================
# COLLABORATIVE FILTERING
# ==========================================
def get_cf_recommendation(target_user, df_trx, fallback_df=None, item_col='merchant_name', n_neighbors=5, top_n=3):
    def use_fallback():
        if fallback_df is None or fallback_df.empty:
            return pd.DataFrame(columns=[item_col, 'score'])

        user_data = df_trx[df_trx['no_rek'] == target_user]
        if not user_data.empty and 'cluster' in user_data.columns:
            user_cluster = user_data['cluster'].iloc[0]
            fallback_recs = fallback_df[fallback_df['cluster'] == user_cluster].head(top_n)
            res = fallback_recs[[item_col, 'total_transaksi']].copy()
            res.rename(columns={'total_transaksi': 'score'}, inplace=True)
            return res
        return pd.DataFrame(columns=[item_col, 'score'])

    df_filtered = df_trx[df_trx['status'] == 'sukses']

    if target_user not in df_filtered['no_rek'].values:
        return use_fallback()

    user_item_matrix = df_filtered.groupby(['no_rek', item_col]).size().unstack(fill_value=0)

    if target_user not in user_item_matrix.index:
        return use_fallback()

    similarity_matrix = cosine_similarity(user_item_matrix)
    df_user_sim = pd.DataFrame(
        similarity_matrix,
        index=user_item_matrix.index,
        columns=user_item_matrix.index
    )

    similar_users = df_user_sim[target_user].sort_values(ascending=False)[1:n_neighbors + 1].index
    similar_users_trx = user_item_matrix.loc[similar_users].sum(axis=0)
    target_user_trx = user_item_matrix.loc[target_user]

    recommendations = similar_users_trx[target_user_trx == 0]
    top_recommendations = recommendations.sort_values(ascending=False).head(top_n)

    if top_recommendations.sum() == 0:
        top_recommendations = similar_users_trx.sort_values(ascending=False).head(top_n)

    result = top_recommendations[top_recommendations > 0].reset_index()
    result.columns = [item_col, 'score']
    return result


# ==========================================
# CONTENT BASED FILTERING
# ==========================================
def compute_weighted_score(user_profile, item_row, common_cols, w_channel=0.5, w_kategori=0.5):
    score = 0
    for col in common_cols:
        if col.startswith("channel_"):
            score += w_channel * user_profile.get(col, 0) * item_row.get(col, 0)
        elif col.startswith("kategori_"):
            score += w_kategori * user_profile.get(col, 0) * item_row.get(col, 0)
    return score


def cbf_engine(user_id, df_trx, catalog, item_name, channel_weight=0.5, kategori_weight=0.5, top_n=3):
    df_filtered = df_trx[df_trx['status'] == 'sukses']
    user_data = df_filtered[df_filtered['no_rek'] == user_id]

    if user_data.empty:
        return pd.DataFrame()

    encoder = OneHotEncoder(handle_unknown='ignore')
    user_encoded = encoder.fit_transform(user_data[['channel', 'kategori']])
    user_feature_names = encoder.get_feature_names_out(['channel', 'kategori'])
    df_user = pd.DataFrame(user_encoded.toarray(), columns=user_feature_names)
    user_profile = df_user.mean(axis=0)

    encoder_item = OneHotEncoder(handle_unknown='ignore')
    item_encoded = encoder_item.fit_transform(catalog[['channel', 'kategori']])
    item_feature_names = encoder_item.get_feature_names_out(['channel', 'kategori'])
    df_item = pd.DataFrame(item_encoded.toarray(), columns=item_feature_names)
    df_item[item_name] = catalog[item_name].values

    common_cols = list(set(user_profile.index) & set(df_item.columns))

    scores = []
    explanations = []
    for _, row in df_item.iterrows():
        score = compute_weighted_score(user_profile, row, common_cols, channel_weight, kategori_weight)
        scores.append(score)

        top_features = sorted(
            [(col, user_profile.get(col, 0) * row.get(col, 0)) for col in common_cols],
            key=lambda x: x[1], reverse=True
        )[:3]
        explanations.append(top_features)

    df_item['score'] = scores
    df_item['explanation'] = explanations
    df_result = df_item[[item_name, 'score', 'explanation']].sort_values('score', ascending=False)
    return df_result.head(top_n)

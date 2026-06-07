from sqlalchemy import text
from src.database import engine


def get_dashboard_stats():

    with engine.connect() as conn:

        total_users = conn.execute(
            text("SELECT COUNT(*) FROM users")
        ).scalar()

        total_transactions = conn.execute(
            text("SELECT COUNT(*) FROM transactions")
        ).scalar()

        total_interactions = conn.execute(
            text("SELECT (SELECT COUNT(*) FROM feature_clicks) + (SELECT COUNT(*) FROM recommendation_clicks)")
        ).scalar()

        total_recommendations = conn.execute(
            text("SELECT COUNT(*) FROM recommendations")
        ).scalar()

        top_merchants = conn.execute(
            text("""
                SELECT merchant_name,
                       COUNT(*) AS total
                FROM transactions
                WHERE status = 'SUCCESS' AND merchant_name IS NOT NULL
                GROUP BY merchant_name
                ORDER BY total DESC
                LIMIT 5
            """)
        ).fetchall()

        return {
            "total_users": total_users,
            "total_transactions": total_transactions,
            "total_interactions": total_interactions,
            "total_recommendations": total_recommendations,
            "top_merchants": [
                {
                    "merchant": row[0],
                    "total": row[1]
                }
                for row in top_merchants
            ]
        }
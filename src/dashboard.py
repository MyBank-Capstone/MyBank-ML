from sqlalchemy import text
from src.database import engine


def get_dashboard_stats():

    with engine.connect() as conn:

        total_users = conn.execute(
            text("SELECT COUNT(*) FROM accounts")
        ).scalar()

        total_transactions = conn.execute(
            text("SELECT COUNT(*) FROM transactions")
        ).scalar()

        total_interactions = conn.execute(
            text("SELECT COUNT(*) FROM interactions")
        ).scalar()

        total_recommendations = conn.execute(
            text("SELECT COUNT(*) FROM recommendations")
        ).scalar()

        top_merchants = conn.execute(
            text("""
                SELECT m.merchant_name,
                       COUNT(*) AS total
                FROM transactions t
                JOIN merchants m
                    ON t.merchant_id = m.merchant_id
                WHERE t.status = 'sukses'
                GROUP BY m.merchant_name
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
from sqlalchemy import text
from src.database import engine


def get_recommendation_history(user_id):

    with engine.connect() as conn:

        rows = conn.execute(
            text("""
                SELECT
                    recommendation_id,
                    recommendation_type,
                    recommendation_item,
                    score,
                    explanation,
                    created_at
                FROM recommendations
                WHERE no_rek = :user_id
                ORDER BY created_at DESC
            """),
            {
                "user_id": user_id
            }
        ).mappings().all()

    return [dict(row) for row in rows]
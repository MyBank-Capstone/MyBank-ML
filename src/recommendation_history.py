from sqlalchemy import text
from src.database import engine


def get_recommendation_history(user_id):

    with engine.connect() as conn:

        rows = conn.execute(
            text("""
                SELECT
                    id AS recommendation_id,
                    type AS recommendation_type,
                    title AS recommendation_item,
                    description AS score_info,
                    reason AS explanation,
                    created_at
                FROM recommendations
                WHERE user_id = :user_id
                ORDER BY created_at DESC
            """),
            {
                "user_id": user_id
            }
        ).mappings().all()

    return [dict(row) for row in rows]
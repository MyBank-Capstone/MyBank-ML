from sqlalchemy import text
from src.database import engine

def save_recommendation(
    user_id,
    recommendation_type,
    recommendation_item,
    score,
    explanation
):
    if "PROMO" in recommendation_type:
        db_type = 'PROMO'
    elif "FEATURE" in recommendation_type:
        db_type = 'FEATURE'
    else:
        db_type = 'PRODUCT'

    with engine.begin() as conn:
        conn.execute(
            text("""
                INSERT INTO recommendations
                (
                    user_id,
                    type,
                    title,
                    description,
                    reason
                )
                VALUES
                (
                    :user_id,
                    :type,
                    :title,
                    :description,
                    :reason
                )
            """),
            {
                "user_id": user_id,
                "type": db_type,
                "title": recommendation_item,
                "description": f"Score: {score:.4f}",
                "reason": str(explanation)
            }
        )
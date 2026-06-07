from sqlalchemy import text
from src.database import engine

def save_recommendation(
    no_rek,
    recommendation_type,
    recommendation_item,
    score,
    explanation
):
    with engine.begin() as conn:
        conn.execute(
            text("""
                INSERT INTO recommendations
                (
                    no_rek,
                    recommendation_type,
                    recommendation_item,
                    score,
                    explanation
                )
                VALUES
                (
                    :no_rek,
                    :recommendation_type,
                    :recommendation_item,
                    :score,
                    :explanation
                )
            """),
            {
                "no_rek": no_rek,
                "recommendation_type": recommendation_type,
                "recommendation_item": recommendation_item,
                "score": float(score),
                "explanation": explanation
            }
        )
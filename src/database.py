import os
from sqlalchemy import create_engine
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "mysql+pymysql://root@localhost:3306/mybank_db"
)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True
)
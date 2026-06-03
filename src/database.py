from sqlalchemy import create_engine

DATABASE_URL = (
    "mysql+pymysql://root:root@localhost:3306/mybank"
)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True
)
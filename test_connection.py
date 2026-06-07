import pandas as pd
from src.database import engine

df = pd.read_sql("SELECT 1 as test", engine)

print(df)
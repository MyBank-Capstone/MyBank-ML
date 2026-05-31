import pandas as pd
from src.database import engine

# Accounts
accounts = pd.read_csv("data/Accounts_Final.csv")
accounts = accounts.where(pd.notnull(accounts), None)

accounts.to_sql(
    "accounts",
    engine,
    if_exists="append",
    index=False
)

print("Accounts imported")

# Merchants
merchants = pd.read_csv("data/Merchants.csv")
merchants = merchants.where(pd.notnull(merchants), None)

merchants.to_sql(
    "merchants",
    engine,
    if_exists="append",
    index=False
)

print("Merchants imported")

# Transactions
transactions = pd.read_csv("data/Transactions_Final.csv")
transactions = transactions.where(pd.notnull(transactions), None)

transactions.to_sql(
    "transactions",
    engine,
    if_exists="append",
    index=False
)

print("Transactions imported")

# Interactions
interactions = pd.read_csv("data/Interactions_Final.csv")
interactions = interactions.where(pd.notnull(interactions), None)

interactions.to_sql(
    "interactions",
    engine,
    if_exists="append",
    index=False
)

print("Interactions imported")
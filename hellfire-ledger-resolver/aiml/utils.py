import random

users = ["Utkarsh", "Ayush", "Muskan", "Sujay"]

random.seed(42)

def generate_transactions(df, amount_column, limit=10):

    transactions = []

    for amount in df[amount_column].head(limit):

        payer = random.choice(users)
        receiver = random.choice(users)

        if payer != receiver:
            transactions.append((payer, receiver, amount))

    return transactions
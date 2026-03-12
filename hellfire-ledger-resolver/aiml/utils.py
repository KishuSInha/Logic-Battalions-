import random

users = ["Utkarsh", "Ayush", "Muskan", "Sujay"]

def generate_transactions(df, limit=10):

    transactions = []

    for amount in df["Amount"].head(limit):

        payer = random.choice(users)
        receiver = random.choice(users)

        if payer != receiver:
            transactions.append((payer, receiver, amount))

    return transactions
import pandas as pd

def load_and_clean_data(file_path):

    df = pd.read_csv(file_path)

    # Remove rows with missing amount
    df = df.dropna(subset=["Amount"])

    # Convert amount to numeric
    df["Amount"] = pd.to_numeric(df["Amount"], errors="coerce")

    # Drop invalid rows
    df = df.dropna()

    return df
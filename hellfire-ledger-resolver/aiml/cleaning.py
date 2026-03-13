import pandas as pd

def load_and_clean_data(file_path):

    df = pd.read_csv(file_path)

    # find numeric columns
    numeric_cols = df.select_dtypes(include=["number"]).columns

    if len(numeric_cols) == 0:
        raise ValueError("No numeric column found in CSV")

    # use the first numeric column as amount
    amount_column = numeric_cols[0]

    df = df.dropna(subset=[amount_column])

    df[amount_column] = pd.to_numeric(df[amount_column], errors="coerce")

    df = df.dropna()

    return df, amount_column
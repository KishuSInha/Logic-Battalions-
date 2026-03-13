import json
from cleaning import load_and_clean_data
from utils import generate_transactions
from optimizer import optimize_settlements

def main():

    df, amount_column = load_and_clean_data("debts.csv")

    transactions = generate_transactions(df, amount_column)

    settlements = optimize_settlements(transactions)

    result = [s.to_dict() for s in settlements]

    output = {"settlements": result}

    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
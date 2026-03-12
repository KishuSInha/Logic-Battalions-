import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from optimizer import optimize_settlements


def test_simple_case():

    transactions = [
        ("Alice","Bob",100),
        ("Bob","Charlie",100)
    ]

    settlements = optimize_settlements(transactions)

    assert len(settlements) == 1

    s = settlements[0]

    assert s.debtor == "Alice"
    assert s.creditor == "Charlie"
    assert s.amount == 100

    print("Test passed!")

test_simple_case()
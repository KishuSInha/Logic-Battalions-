class Settlement:

    def __init__(self, debtor, creditor, amount):
        self.debtor = debtor
        self.creditor = creditor
        self.amount = amount

    def to_dict(self):
        return {
            "from": self.debtor,
            "to": self.creditor,
            "amount": round(self.amount, 2)
        }
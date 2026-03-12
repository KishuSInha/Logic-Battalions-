from schema import Settlement

def optimize_settlements(transactions):

    balances = {}

    for payer, receiver, amount in transactions:

        balances[payer] = balances.get(payer, 0) - amount
        balances[receiver] = balances.get(receiver, 0) + amount

    debtors = []
    creditors = []

    for person, balance in balances.items():

        if balance < 0:
            debtors.append([person, -balance])

        elif balance > 0:
            creditors.append([person, balance])

    settlements = []

    i = 0
    j = 0

    while i < len(debtors) and j < len(creditors):

        debtor, debt = debtors[i]
        creditor, credit = creditors[j]

        payment = min(debt, credit)

        settlements.append(Settlement(debtor, creditor, payment))

        debtors[i][1] -= payment
        creditors[j][1] -= payment

        if debtors[i][1] == 0:
            i += 1

        if creditors[j][1] == 0:
            j += 1

    return settlements
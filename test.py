from copy import deepcopy


class Purchase:
    def __init__(self, from_currency, to_currency, from_amount, to_amount):
        self.from_currency = from_currency
        self.to_currency = to_currency
        self.initial_from_amount = from_amount
        self.from_amount = from_amount
        self.to_amount = to_amount
        self.rate = to_amount / from_amount

class Deal:
    def __init__(self, from_currency, to_currency, from_amount, to_amount):
        self.from_currency = from_currency
        self.to_currency = to_currency
        self.from_amount = from_amount
        self.to_amount = to_amount

    def profit(self, purchase):
        remaining_rate = purchase.to_amount / purchase.from_amount
        if self.from_currency == purchase.from_currency:
            rate = remaining_rate
        else:
            rate = 1 / remaining_rate
        return (rate - self.to_amount / self.from_amount) * self.from_amount / rate

purchases = [
    Purchase('DOLLAR', 'RUB', 1, 79),
    Purchase('DOLLAR', 'RUB', 1, 79),
]
purchases.reverse()

deals = [
    Deal('DOLLAR', 'RUB', 4, 158),
    Deal('RUB', 'DOLLAR', 158, 1)
]

# Assume you always purchase before you deal
balances = {'DOLLAR': 0, 'RUB': 0}
profits = [0 for _ in deals]

for purchase in purchases:
    balances[purchase.to_currency] += purchase.to_amount

for i, deal in enumerate(deals):
    remaining_amount = deal.from_amount
    idx = 0
    saved_purchases = deepcopy(purchases)
    while remaining_amount > 0 and idx < len(saved_purchases):
        purchase = saved_purchases[idx]
        if purchase.to_currency == deal.from_currency or purchase.from_currency == deal.from_currency:
            if remaining_amount <= purchase.to_amount:
                profits[i] += deal.profit(purchase) * remaining_amount / deal.from_amount
                purchase.to_amount -= remaining_amount
                remaining_amount = 0
            else:
                profits[i] += deal.profit(purchase) * purchase.to_amount / deal.from_amount
                remaining_amount -= purchase.to_amount
                purchase.to_amount = 0
        idx += 1
    balances[deal.from_currency] += deal.from_amount
    balances[deal.to_currency] -= deal.to_amount

for i, profit in enumerate(profits):
    print(f'Profit for deal {i + 1}: {profit}')

print(f'Final balances: {balances}')

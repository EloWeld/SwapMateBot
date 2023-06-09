import datetime
from loader import *
from models.deal import Deal
from models.etc import Currency


def test_calculate_profit_no_buying_currencies(capsys):
    # Test when there are no buying currencies available
    deal = Deal(0, 1, 6069303965, 6069303965, 
                20, Currency.objects.get({"symbol": "USDT"}),
                Currency.objects.get({"symbol": "RUB"}),
                None, None, "FINISHED", 83, None, datetime.datetime.now()
    
    )
    profit = deal.calculate_profit()
    print(profit)
    assert profit == 492.59259259259215
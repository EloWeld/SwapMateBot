from pymodm import MongoModel, fields
from pymongo.write_concern import WriteConcern

class Currency(MongoModel):
    id = fields.IntegerField(primary_key=True)
    is_crypto = fields.BooleanField(default=False)
    symbol = fields.CharField(blank=False)
    verbose_name = fields.CharField(blank=True)
    is_available = fields.BooleanField(default=True)
    rub_rate = fields.FloatField(blank=False, default=1.0)
    pool_balance = fields.FloatField(blank=False, default=0.0)
    
    class Meta:
        write_concern = WriteConcern(j=True)
        connection_alias = 'pymodm-conn'
        collection_name = 'Currencies'
        
        
# cc = Currency(1, False, "BAT", "BAT", True, 1.0, 0)
# cc.save()
# cc = Currency(2, False, "RUB", "RUB", True, 1.0, 0)
# cc.save()
# cc = Currency(3, False, "CNY", "CNY", True, 1.0, 0)
# cc.save()
# cc = Currency(4, False, "USD", "USD", True, 1.0, 0)
# cc.save()
# cc = Currency(5, True, "USDT", "USDT", True, 1.0, 0)
# cc.save()
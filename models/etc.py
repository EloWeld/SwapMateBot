from pymodm import MongoModel, fields
from pymongo.write_concern import WriteConcern

class Currency(MongoModel):
    id = fields.IntegerField(primary_key=True)
    types = fields.ListField(fields.CharField(default="ФИЗЛИЦО"), blank=True)
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

    def rate_with(self, sub: 'Currency'):
        return 1 / ( self.rub_rate / sub.rub_rate)

        
# cc = Currency(1, ["Физлицо"], False, "BAT", "BAT", True, 1.0, 0)
# cc.save()
# cc = Currency(2, [], False, "RUB", "RUB", True, 1.0, 0)
# cc.save()
# cc = Currency(3, ["Физлицо", "Алим", "Вичат", "Юрлицо"], False, "CNY", "CNY", True, 1.0, 0)
# cc.save()
# cc = Currency(4, ["Юрлицо Китай", "Юрлицо Гк"], False, "USD", "USD", True, 1.0, 0)
# cc.save()
# cc = Currency(5, [], True, "USDT", "USDT", True, 1.0, 0)
# cc.save()


class City(MongoModel):
    id = fields.CharField(primary_key=True)
    name = fields.CharField(blank=False, default="Другой")
    
    class Meta:
        write_concern = WriteConcern(j=True)
        connection_alias = 'pymodm-conn'
        collection_name = 'City'


cy = City(id="Moscow", name="Москва")
cy.save()

cy = City(id="Kransnoyarsk", name="Красноярск")
cy.save()

cy = City(id="Sochi", name="Сочи")
cy.save()
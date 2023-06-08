from pymodm import MongoModel, fields
from pymongo.write_concern import WriteConcern


class Currency(MongoModel):
    id = fields.IntegerField(primary_key=True)
    types = fields.ListField(fields.CharField(default="ФИЗЛИЦО"), blank=True)
    is_crypto = fields.BooleanField(default=False)
    admin = fields.ReferenceField('TgUser')
    symbol = fields.CharField(blank=False)
    verbose_name = fields.CharField(blank=True)
    is_available = fields.BooleanField(default=True)
    rub_rate = fields.FloatField(blank=False, default=1.0)
    buy_rub_rate = fields.FloatField(blank=False, default=1.0)
    pool_balance = fields.FloatField(blank=False, default=0.0)
    blocked_target_types = fields.ListField(blank=True, default=[])
    blocked_source_types = fields.ListField(blank=True, default=[])
    
    class Meta:
        write_concern = WriteConcern(j=True)
        connection_alias = 'pymodm-conn'
        collection_name = 'Currencies'

    def rate_with(self, sub: 'Currency'):
        return 1 / ( self.rub_rate / sub.rub_rate)
    
    def as_row(self):
        return [
            self.id,
            '; '.join(self.types),
            "Да" if self.is_crypto else "Нет",
            self.symbol,
            "Да" if self.is_available else "Нет",
            round(self.rub_rate, 2),
            self.pool_balance
        ]
        
    
    @staticmethod
    def get_row_headers():
        return [
            "ID",
            "Виды",
            "Является криптой",
            "Символ",
            "Доступна для свапа",
            "Курс к рублю",
            "Количество",
        ]
        
    def with_types(self, only=False):
        if only:
            return "" if len(self.types) == 0 else self.types[0] if len(self.types) == 1 else f"({', '.join(self.types)})"
        else:
            if len(self.types) == 0:
                return self.symbol
            elif len(self.types) == 1:
                return f"{self.symbol} {self.types[0]}"
            else:
                return f"{self.symbol} ({', '.join(self.types)})"
        


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
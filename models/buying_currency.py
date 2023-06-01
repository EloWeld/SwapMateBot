import datetime
from pymodm import MongoModel, fields
from pymongo.write_concern import WriteConcern
from models.etc import Currency

from models.tg_user import TgUser

class BuyingCurrency(MongoModel):
    id = fields.IntegerField(primary_key=True)
    owner: TgUser = fields.ReferenceField(TgUser)
    source_currency: Currency = fields.ReferenceField(Currency)
    target_currency: Currency = fields.ReferenceField(Currency)
    source_amount = fields.FloatField()
    target_amount = fields.FloatField()
    exchange_rate = fields.FloatField()
    created_at: datetime.datetime = fields.DateTimeField()
    
    class Meta:
        write_concern = WriteConcern(j=True)
        connection_alias = 'pymodm-conn'
        collection_name = 'BuyingCurrency'

    def as_row(self):
        return [
            self.id,
            self.owner.id,
            self.source_currency.symbol,
            self.target_currency.symbol,
            self.source_amount,
            self.target_amount,
            self.exchange_rate,
            self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        ]
        
    
    @staticmethod
    def get_row_headers():
        return [
            "ID",
            "Пользователь",
            "Из валюты",
            "В валюту",
            "Отдал",
            "Получил",
            "Курс обмена",
            "Дата и время",
        ]
        
        
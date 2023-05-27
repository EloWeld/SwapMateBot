from pymodm import MongoModel, fields
from pymongo.write_concern import WriteConcern
from models.etc import Currency

from models.tg_user import TgUser

class BuyingCurrency(MongoModel):
    id = fields.IntegerField(primary_key=True)
    owner = fields.ReferenceField(TgUser)
    source_currency = fields.ReferenceField(Currency)
    target_currency = fields.ReferenceField(Currency)
    source_amount = fields.FloatField()
    target_amount = fields.FloatField()
    created_at = fields.DateTimeField()
    exchange_rate = fields.FloatField()
    
    class Meta:
        write_concern = WriteConcern(j=True)
        connection_alias = 'pymodm-conn'
        collection_name = 'BuyingCurrency'
        
        
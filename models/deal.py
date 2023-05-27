from pymodm import MongoModel, fields
from pymongo.write_concern import WriteConcern
from enum import Enum

class Deal(MongoModel):
    class DealStatuses(Enum):
        ACTIVE = "ACTIVE"
        CANCELLED = "CANCELLED"
        FINISHED = "FINISHED"

    id = fields.IntegerField(primary_key=True)
    external_id = fields.IntegerField()
    created_at = fields.DateTimeField()
    deal_value = fields.FloatField()
    currency_symbol_from = fields.CharField(blank=False)
    currency_symbol_to = fields.CharField(blank=False)
    currency_type_from = fields.CharField(blank=True)
    currency_type_to = fields.CharField(blank=True)
    owner_id = fields.IntegerField(blank=False)
    status = fields.CharField(choices=list(DealStatuses.__members__.keys()), default=DealStatuses.ACTIVE.value)
    
    class Meta:
        write_concern = WriteConcern(j=True)
        connection_alias = 'pymodm-conn'
        collection_name = 'Deals'
        
        
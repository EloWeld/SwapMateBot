from pymodm import MongoModel, fields
from pymongo.write_concern import WriteConcern

class Deal(MongoModel):
    id = fields.IntegerField(primary_key=True)
    created_at = fields.DateTimeField()
    currency_symbol_from = fields.CharField(blank=False)
    currency_symbol_to = fields.CharField(blank=False)
    owner_id = fields.IntegerField(blank=False)
    status = fields.CharField(choices=["ACTIVE", "CANCELLED", "FINISHED"], default="ACTIVE")
    
    class Meta:
        write_concern = WriteConcern(j=True)
        connection_alias = 'pymodm-conn'
        collection_name = 'Deals'
        
        
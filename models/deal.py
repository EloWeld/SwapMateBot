from pymodm import MongoModel, fields
from pymongo.write_concern import WriteConcern

class Deal(MongoModel):
    id = fields.IntegerField(primary_key=True)
    created_at = fields.DateTimeField()
    status = fields.CharField(choices=["ACTIVE", "CANCELLED", "FINISHED"])
    
    class Meta:
        write_concern = WriteConcern(j=True)
        connection_alias = 'pymodm-conn'
        collection_name = 'Deals'
        
        
from pymodm import MongoModel, fields
from pymongo.write_concern import WriteConcern

class TgUser(MongoModel):
    id = fields.IntegerField(primary_key=True)
    fullname = fields.CharField(blank=True, default="UnnamedUser")
    username = fields.CharField(blank=True, default="NoUsename")
    isAdmin = fields.BooleanField(default=False)
    
    class Meta:
        write_concern = WriteConcern(j=True)
        connection_alias = 'pymodm-conn'
        collection_name = 'Users'
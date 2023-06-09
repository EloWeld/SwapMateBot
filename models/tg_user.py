import datetime
from typing import Union
from pymodm import MongoModel, fields
from pymongo.write_concern import WriteConcern

from models.etc import City, Currency


class TgUser(MongoModel):
    id = fields.IntegerField(primary_key=True)
    invited_by: Union['TgUser', None] = fields.ReferenceField('TgUser', blank=True)
    fullname = fields.CharField(blank=True, default="UnnamedUser")
    username = fields.CharField(blank=True, default="NoUsename")
    real_name = fields.CharField(blank=True, default="NoName")

    is_admin = fields.BooleanField(blank=False, default=False)

    is_member = fields.BooleanField(blank=False, default=False)
    join_request_status = fields.CharField(blank=False, choices=("NO", "SENT", "DISCARDED", "ACCEPTED"), default="NO")

    balance = fields.FloatField(blank=False, default=0)
    balances = fields.DictField(blank=True, default={"5": 0, "2": 0})
    city: City = fields.ReferenceField(City, blank=True)
    
    personal_data_storage = fields.DictField(blank=True, default={})
    cash_flow = fields.ListField(fields.ReferenceField('CashFlow'), blank=True)
    
    created_at: datetime.datetime = fields.DateTimeField()


    class Meta:
        write_concern = WriteConcern(j=True)
        connection_alias = 'pymodm-conn'
        collection_name = 'Users'
        

def random_owner():
    from models.tg_user import TgUser
    return TgUser.objects.raw({"is_admin": True}).first()
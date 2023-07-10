import datetime
from typing import Union
from pymongo.write_concern import WriteConcern
from pymodm import MongoModel, fields
from enum import Enum

class CashFlow(MongoModel):
    
    class CashFlowType(Enum):
        REFILL_BALANCE = "ПОПОЛНЕНИЕ СЧЁТА"
        SWAP = "СВАП"
        BALANCE_EDIT = "ИЗМЕНЕНИЕ БАЛАНСА"
    
    id = fields.IntegerField(primary_key=True)
    user = fields.ReferenceField('TgUser', blank=True)
    type = fields.CharField(choices=list(CashFlowType.__members__.keys()), blank=False)
    source_currency = fields.ReferenceField('Currency', default=0, blank=True)
    target_currency = fields.ReferenceField('Currency', default=0, blank=True)
    source_amount = fields.FloatField(blank=True, default=0)
    target_amount = fields.FloatField(blank=True, default=0)
    additional_data = fields.CharField(default="")
    additional_amount = fields.FloatField(blank=True, default=0)
    source_currency_type = fields.CharField(default="")
    target_currency_type = fields.CharField(default="")

    created_at: datetime.datetime = fields.DateTimeField(blank=False)
    
    class Meta:
        write_concern = WriteConcern(j=True)
        connection_alias = 'pymodm-conn'
        collection_name = 'CashFlow'
        
        
    @staticmethod
    def get_row_headers():
        return [
            "ID",
            "Тип",
            "Исходная валюта",
            "Кол-во",
            "Конечная валюта",
            "Кол-во",
            "Доп. данные",
            "Доп. количетсво",
            "Дата и время",
        ]
    
    def as_row(self):
        return [
            self.id,
            getattr(self.CashFlowType, self.type).value,
            self.source_currency.symbol + " " + self.source_currency_type if self.source_currency else "",
            round(self.source_amount, 2),
            self.target_currency.symbol + " " + self.target_currency_type if self.target_currency else "",
            round(self.target_amount, 2),
            self.additional_data,
            round(self.additional_amount, 2),
            self.created_at.strftime('%d.%m.%Y %H:%M:%S'),
        ]
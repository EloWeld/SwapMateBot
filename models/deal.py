import datetime
from typing import List
from pymodm import MongoModel, fields
from pymongo.write_concern import WriteConcern
from enum import Enum
from models.etc import Currency

from models.tg_user import TgUser

class Deal(MongoModel):
    class DealStatuses(Enum):
        ACTIVE = "ACTIVE"
        CANCELLED = "CANCELLED"
        FINISHED = "FINISHED"

    id = fields.IntegerField(primary_key=True)
    external_id = fields.IntegerField()
    admin: TgUser = fields.ReferenceField(TgUser)
    owner: TgUser = fields.ReferenceField(TgUser)
    deal_value = fields.FloatField()
    currency_from: Currency = fields.ReferenceField(Currency)
    currency_to: Currency = fields.ReferenceField(Currency)
    currency_type_from = fields.CharField(blank=True)
    currency_type_to = fields.CharField(blank=True)
    status = fields.CharField(choices=list(DealStatuses.__members__.keys()), default=DealStatuses.ACTIVE.value)
    rate = fields.FloatField(blank=False)
    profit = fields.FloatField(blank=False, default=0)
    additional_info = fields.CharField(blank=True)
    created_at: datetime.datetime = fields.DateTimeField()
    
    class Meta:
        write_concern = WriteConcern(j=True)
        connection_alias = 'pymodm-conn'
        collection_name = 'Deals'

    def dir_text(self, with_values = False, tag="code", remove_currency_type=False):
        if with_values:
            return f"<{tag}>{self.deal_value:.4f}</{tag}> {self.currency_from.symbol} ➡️ <{tag}>{self.rate*self.deal_value:.4f}</{tag}> {self.currency_to.symbol}"
        else:
            return f"{self.currency_from.symbol}{'' if not self.currency_type_from or remove_currency_type else f' {self.currency_type_from}'} ➡️ {self.currency_to.symbol}{'' if not self.currency_type_to or remove_currency_type else f' {self.currency_type_to}'}"
        
    def get_rate_text(self, tag="code"):
        return f"<{tag}>{1}</{tag}> <{tag}>{self.currency_from.symbol}</{tag}> = <{tag}>{self.rate:.4f}</{tag}> <{tag}>{self.currency_to.symbol}</{tag}>"
    
    def get_full_external_id(self):
        date = self.created_at if self.created_at else self.datetime(
            1970, 1, 1, 0, 0)
        return f"{date.month:02}{self.external_id:02}"
        
    def as_row(self) -> list:
        return [
            self.id,
            self.get_full_external_id(),
            self.status,
            self.currency_from.symbol,
            self.currency_type_from,
            self.currency_to.symbol,
            self.currency_type_to,
            f"{self.owner.id} @{self.owner.username} @{self.owner.real_name}",
            self.deal_value,
            self.rate * self.deal_value,
            self.rate,
            self.profit,
            self.additional_info,
            self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        ]
    
    @staticmethod
    def get_row_headers():
        return [
            "ID",
            "Внешний ID",
            "Статус",
            "Из валюты",
            "(Тип) Из валюты",
            "В валюту",
            "(Тип) В валюту",
            "Пользователь",
            "Отдал",
            "Получил",
            "Профит",
            "Доп. информация",
            "Дата и время свапа",
        ]
    
    def calculate_profit(self, bc_list=[]):
        from models.buying_currency import BuyingCurrency
        from pymongo import DESCENDING, ASCENDING
        profit = 0
        if bc_list:
            buying_currencies = bc_list
        else:
            buying_currencies: List[BuyingCurrency] = BuyingCurrency.objects.raw({"$or": [
                {"$and": [{"source_currency": self.currency_from.id}, {"target_currency": self.currency_to.id},] },
                {"$and": [{"target_currency": self.currency_from.id}, {"source_currency": self.currency_to.id}]}]}).order_by([('created_at', DESCENDING)])
        for bc in buying_currencies:
            exrate = bc.exchange_rate if bc.source_currency.id == self.currency_from.id else 1 / bc.exchange_rate
            dv = min(bc.target_amount, self.deal_value)
            profit += dv / exrate - dv / self.rate
            self.deal_value -= bc.target_amount
            if self.deal_value <= 0:
                break
        if self.deal_value >=0:
            return 0
        return profit



        
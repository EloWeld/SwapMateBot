import datetime
from typing import List
from pymodm import MongoModel, fields
from pymongo.write_concern import WriteConcern
from enum import Enum
from etc.texts import BOT_TEXTS
from models.etc import Currency

from models.tg_user import TgUser

class Deal(MongoModel):
    class DealStatuses(Enum):
        ACTIVE = "ACTIVE"
        CANCELLED = "CANCELLED"
        FINISHED = "FINISHED"

    id = fields.IntegerField(primary_key=True)
    external_id = fields.IntegerField()
    dir = fields.CharField(blank=True, default="wanna_give")
    admin: TgUser = fields.ReferenceField(TgUser)
    owner: TgUser = fields.ReferenceField(TgUser)
    deal_value = fields.FloatField()
    source_currency: Currency = fields.ReferenceField(Currency)
    target_currency: Currency = fields.ReferenceField(Currency)
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

    def dir_text(self, with_values = False, tag="code", remove_currency_type=False, format_html_tag=True):
        if format_html_tag:
            if with_values:
                return f"<{tag}>{self.deal_value:.2f}</{tag}> {self.source_currency.symbol} ➡️ <{tag}>{self.rate*self.deal_value:.2f}</{tag}> {self.target_currency.symbol}"
            else:
                return f"{self.source_currency.symbol}{'' if not self.currency_type_from or remove_currency_type else f' {self.currency_type_from}'} ➡️ {self.target_currency.symbol}{'' if not self.currency_type_to or remove_currency_type else f' {self.currency_type_to}'}"
        else:
            if with_values:
                return f"{self.deal_value:.2f} {self.source_currency.symbol} ➡️ {self.rate*self.deal_value:.2f} {self.target_currency.symbol}"
            else:
                return f"{self.source_currency.symbol}{'' if not self.currency_type_from or remove_currency_type else f' {self.currency_type_from}'} ➡️ {self.target_currency.symbol}{'' if not self.currency_type_to or remove_currency_type else f' {self.currency_type_to}'}"
            
            
            
    def get_rate_text(self, tag="code"):
        if self.rate >= 1:
            return f"<{tag}>{1}</{tag}> <{tag}>{self.source_currency.symbol}</{tag}>=<{tag}>{self.rate:.2f}</{tag}> <{tag}>{self.target_currency.symbol}</{tag}>"
        else:
            return f"<{tag}>{1}</{tag}> <{tag}>{self.target_currency.symbol}</{tag}>=<{tag}>{1/self.rate:.2f}</{tag}> <{tag}>{self.source_currency.symbol}</{tag}>"
    
    def get_full_external_id(self):
        date = self.created_at if self.created_at else self.datetime(
            1970, 1, 1, 0, 0)
        return f"{date.month:02}{self.external_id:02}"
        
    def as_row(self) -> list:
        return [
            self.id,
            self.get_full_external_id(),
            self.status,
            self.source_currency.symbol,
            self.currency_type_from,
            self.target_currency.symbol,
            self.currency_type_to,
            f"{self.owner.id} @{self.owner.username} @{self.owner.real_name}",
            round(self.deal_value, 2),
            round(self.rate * self.deal_value, 2),
            round(self.rate if self.rate > 1 else 1/self.rate, 2),
            round(self.profit, 2),
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
            "Курс свапа",
            "Профит",
            "Доп. информация",
            "Дата и время свапа",
        ]
    
    def profit_with(self, purchase):
        if self.source_currency == purchase.source_currency:
            rate = purchase.exchange_rate
        else:
            rate = 1 / purchase.exchange_rate
        return (rate - (self.deal_value * self.rate) / self.deal_value) * self.deal_value / rate
    
    def calculate_profit(self, bc_list=[]):
        from models.buying_currency import BuyingCurrency
        from pymongo import DESCENDING, ASCENDING
        profit = 0
        ddv = self.deal_value
        if bc_list:
            buying_currencies = bc_list
        else:
            buying_currencies: List[BuyingCurrency] = BuyingCurrency.objects.raw({"$or": [
                {"$and": [{"source_currency": self.source_currency.id}, {"target_currency": self.target_currency.id},] },
                {"$and": [{"target_currency": self.source_currency.id}, {"source_currency": self.target_currency.id}]}]}).order_by([('created_at', DESCENDING)])
            
        remaining_amount = self.deal_value
        idx = 0
        profit_parts = []
        while remaining_amount > 0 and idx < buying_currencies.count():
            purchase = buying_currencies[idx]
            if purchase.target_currency == self.source_currency or purchase.source_currency == self.source_currency:
                if remaining_amount <= purchase.target_amount:
                    profit_parts.append(self.profit_with(purchase) * remaining_amount / self.deal_value)
                    purchase.target_amount -= remaining_amount
                    remaining_amount = 0
                else:
                    profit_parts.append(self.profit_with(purchase) * purchase.target_amount / self.deal_value)
                    remaining_amount -= purchase.target_amount
                    purchase.target_amount = 0
            idx += 1
        return sum(profit_parts)


    def get_user_text(self):
        return (f"💠 Свап <code>{self.id}</code>\n\n"
                                  f"🚦 Статус: <code>{BOT_TEXTS.verbose[self.status]}</code>\n"
                                  f"💱 Направление: <code>{self.dir_text()}</code>\n"
                                  f"💱 Обмен: {self.dir_text(with_values=True, tag='b')}\n"
                                  f"💱 Курс: {self.get_rate_text()}\n"
                                  f"📅 Дата создания: <code>{str(self.created_at)[:-7]}</code>\n")
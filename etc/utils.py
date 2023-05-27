import datetime
from typing import List
import loguru
import pymodm
import requests
from loader import MDB, bot
from models.deal import Deal
from models.etc import Currency
from models.tg_user import TgUser
from pymodm import MongoModel


def rate_to_str(c1, c2, rate, postfix=""):
    return f"1 {c2}{postfix} = {rate} {c1}"

async def notifyAdmins(text: str):
    admins: List[TgUser] = TgUser.objects.raw({"is_admin": True})

    for admin in admins:
        try:
            await bot.send_message(admin.id, text)
        except Exception as e:
            loguru.logger.error(f"Can't send message to admin: {e}")


def split_long_text(text: str, max_length: int = 4000):
    parts = []
    while len(text) > max_length:
        split_position = text.rfind('\n', 0, max_length)
        if split_position == -1:
            split_position = max_length
        part = text[:split_position]
        parts.append(part)
        text = text[split_position:]
    parts.append(text)
    return parts


def get_rates_text():
    currencies: List[Currency] = Currency.objects.raw({"is_available": True})
    rates_text = ""
    for currency in currencies:
        rates_text += rate_to_str('RUB', currency.symbol, currency.rub_rate,
                                  ' (crypto)' if currency.is_crypto else '') + "\n"

    r = requests.get("https://www.cbr-xml-daily.ru/latest.js").json()['rates']

    rates_text += f"\nКурс ЦБ:\n"\
        f"{rate_to_str('RUB', 'CNY', round(1/r['CNY'], 4))}\n"\
        f"{rate_to_str('RUB', 'USD', round(1/r['USD'], 4))}\n"

    return rates_text

from pymongo import DESCENDING
def get_max_id_doc(model: MongoModel, condition={}):
    try:
        # Сортируем в обратном порядке (так получим максимальный id) и выбираем первый элемент
        max_id_document = model.objects.raw(condition).order_by([('_id', DESCENDING)]).first()
        max_id = max_id_document
    except model.DoesNotExist:
        # Если нет такого элемента, возвращаем None
        max_id = None
    return max_id

def find_next_month(date: datetime.datetime):
    # Получаем текущий месяц
    current_month = date.month

    # Получаем следующий месяц
    next_month = current_month + 1

    # Проверяем, если следующий месяц больше 12, то переходим на следующий год
    if next_month > 12:
        next_month = 1
        next_year = date.year + 1
    else:
        next_year = date.year

    # Возвращаем следующий месяц
    return datetime.datetime(next_year, next_month, 1, 0, 0, 0, 0)

def find_month_start(date: datetime.datetime):
    # Получаем текущую дату
    current_date = datetime.datetime.now()

    # Получаем первый день текущего месяца
    first_day = datetime.datetime(current_date.year, current_date.month, 1, 0, 0, 0, 0)

    return first_day

def gen_deal_ext_id(deal: Deal):
    return f"{deal.created_at.month:02}{deal.external_id:02}"
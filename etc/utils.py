from typing import List
import loguru
import requests
from loader import MDB, bot
from models.etc import Currency
from models.tg_user import TgUser


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

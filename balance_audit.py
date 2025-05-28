#!/usr/bin/env python3
"""
Скрипт для аудита балансов пользователей
Проверяет соответствие текущих балансов и истории операций (CashFlow)
"""

from models.etc import Currency
from models.cash_flow import CashFlow
from models.tg_user import TgUser
import os
import sys
from dotenv import load_dotenv
from pymodm.connection import connect
from pymongo import MongoClient

# Загружаем переменные окружения
load_dotenv()

# Подключение к MongoDB
MONGODB_CONNECTION_URI = os.environ["MongoConnectionString"]
MONGO_DB_NAME = os.environ["MongoDatabaseName"]

MDB = MongoClient(MONGODB_CONNECTION_URI).get_database(MONGO_DB_NAME)
connect(MONGODB_CONNECTION_URI+f'/{MONGO_DB_NAME}?authSource=admin', alias="pymodm-conn")

# Импортируем модели после подключения к БД


def audit_user_balance(user_id: int):
    """Проверяет баланс конкретного пользователя"""
    print(f"\n🔍 АУДИТ ПОЛЬЗОВАТЕЛЯ {user_id}")
    print("="*50)

    try:
        user = TgUser.objects.get({"_id": user_id})
    except:
        print(f"❌ Пользователь {user_id} не найден")
        return

    print(f"👤 Имя: {user.real_name}")
    print(f"📱 Username: @{user.username}")

    # Получаем все операции пользователя
    cash_flows = list(CashFlow.objects.raw({"user": user_id}))
    cash_flows.sort(key=lambda x: x.created_at)

    print(f"\n📊 Всего операций: {len(cash_flows)}")
    print("\n📈 ИСТОРИЯ ОПЕРАЦИЙ:")
    print("-"*80)

    # Вычисляем баланс по операциям
    calculated_balances = {}

    for cf in cash_flows:
        date_str = cf.created_at.strftime('%d.%m.%Y %H:%M:%S')

        if cf.type == "ПОПОЛНЕНИЕ СЧЁТА":
            currency_id = str(cf.target_currency.id)
            if currency_id not in calculated_balances:
                calculated_balances[currency_id] = 0
            calculated_balances[currency_id] += cf.additional_amount

            print(f"💰 {date_str} | ПОПОЛНЕНИЕ | +{cf.additional_amount} {cf.target_currency.symbol}")

        elif cf.type == "ИЗМЕНЕНИЕ БАЛАНСА":
            currency_id = str(cf.target_currency.id)
            calculated_balances[currency_id] = cf.target_amount

            print(f"✏️  {date_str} | ИЗМЕНЕНИЕ | {cf.source_amount} → {cf.target_amount} {cf.target_currency.symbol}")

        elif cf.type == "СВАП":
            # При свапе ТОЛЬКО списываем исходную валюту
            # Целевую валюту пользователь получает физически (не на баланс в системе)
            source_id = str(cf.source_currency.id)
            if source_id not in calculated_balances:
                calculated_balances[source_id] = 0
            calculated_balances[source_id] -= cf.source_amount

            print(f"🔄 {date_str} | СВАП | -{cf.source_amount} {cf.source_currency.symbol} (получил {cf.target_amount} {cf.target_currency.symbol} физически)")

    print("\n📊 СРАВНЕНИЕ БАЛАНСОВ:")
    print("-"*80)

    # Получаем все валюты для отображения символов
    currencies = {str(c.id): c.symbol for c in Currency.objects.all()}

    # Сравниваем вычисленные и фактические балансы
    all_currency_ids = set(calculated_balances.keys()) | set(user.balances.keys())

    has_discrepancy = False

    for currency_id in all_currency_ids:
        calculated = calculated_balances.get(currency_id, 0)
        actual = user.balances.get(currency_id, 0)
        currency_symbol = currencies.get(currency_id, f"ID_{currency_id}")

        if abs(calculated - actual) > 0.01:  # Допускаем погрешность в 1 копейку
            status = "❌ ОШИБКА"
            has_discrepancy = True
        else:
            status = "✅ ОК"

        print(f"{status} | {currency_symbol}: Вычислено={calculated:.2f}, Фактический={actual:.2f}")

    if has_discrepancy:
        print(f"\n🚨 НАЙДЕНЫ РАСХОЖДЕНИЯ У ПОЛЬЗОВАТЕЛЯ {user_id}!")

        # Показываем детальный разбор для USDT в вашем примере
        usdt_currency = None
        for c in Currency.objects.all():
            if c.symbol == "USDT":
                usdt_currency = c
                break

        if usdt_currency:
            usdt_id = str(usdt_currency.id)
            print(f"\n🔍 ДЕТАЛЬНЫЙ АНАЛИЗ ДЛЯ USDT:")
            print(f"   💰 Пополнения: {sum([cf.additional_amount for cf in cash_flows if cf.type == 'ПОПОЛНЕНИЕ СЧЁТА' and str(cf.target_currency.id) == usdt_id])}")
            print(f"   🔄 Списания по свапам: {sum([cf.source_amount for cf in cash_flows if cf.type == 'СВАП' and str(cf.source_currency.id) == usdt_id])}")
            print(f"   ✏️  Ручные изменения: {[cf for cf in cash_flows if cf.type == 'ИЗМЕНЕНИЕ БАЛАНСА' and str(cf.target_currency.id) == usdt_id]}")

        return False
    else:
        print(f"\n✅ Баланс пользователя {user_id} корректен")
        return True


def audit_all_users():
    """Проверяет балансы всех пользователей"""
    print("🔍 АУДИТ ВСЕХ ПОЛЬЗОВАТЕЛЕЙ")
    print("="*50)

    users = list(TgUser.objects.all())
    total_users = len(users)
    correct_users = 0
    incorrect_users = []

    for user in users:
        if audit_user_balance(user.id):
            correct_users += 1
        else:
            incorrect_users.append(user.id)

    print(f"\n📊 ИТОГОВАЯ СТАТИСТИКА:")
    print("="*50)
    print(f"👥 Всего пользователей: {total_users}")
    print(f"✅ Корректных балансов: {correct_users}")
    print(f"❌ Некорректных балансов: {len(incorrect_users)}")

    if incorrect_users:
        print(f"\n🚨 ПОЛЬЗОВАТЕЛИ С ОШИБКАМИ:")
        for user_id in incorrect_users:
            user = TgUser.objects.get({"_id": user_id})
            print(f"   • {user_id} (@{user.username}) - {user.real_name}")


def main():
    if len(sys.argv) > 1:
        # Аудит конкретного пользователя
        user_id = int(sys.argv[1])
        audit_user_balance(user_id)
    else:
        # Аудит всех пользователей
        audit_all_users()


if __name__ == "__main__":
    main()

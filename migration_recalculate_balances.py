#!/usr/bin/env python3
"""
Миграция для пересчета балансов пользователей на основе CashFlow записей
и исправления некорректных REFILL_BALANCE записей
"""

from models.etc import Currency
from models.cash_flow import CashFlow
from models.tg_user import TgUser
import os
import datetime
import json
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


def calculate_balance_from_cashflow(user_id: int):
    """Рассчитывает баланс пользователя на основе CashFlow записей"""
    cashflows: list[CashFlow] = list(CashFlow.objects.raw({"user": user_id}))
    calculated_balances = {}

    for cf in cashflows:
        if cf.type == CashFlow.CashFlowType.REFILL_BALANCE.name:
            # Пополнение баланса - добавляем сумму пополнения
            if cf.target_currency:
                currency_id = str(cf.target_currency.id)
                if currency_id not in calculated_balances:
                    calculated_balances[currency_id] = 0
                # Используем additional_amount (после исправления это сумма пополнениЯ)
                calculated_balances[currency_id] += cf.additional_amount
                cf.target_amount = calculated_balances[currency_id]
                print(f"🔧 CashFlow #{cf.id}: {currency_id} target_amount/calculated_balances {cf.target_amount}")
                cf.save()

        elif cf.type == CashFlow.CashFlowType.SWAP.name:
            # Свап - списываем исходную валюту
            if cf.source_currency:
                currency_id = str(cf.source_currency.id)
                if currency_id not in calculated_balances:
                    calculated_balances[currency_id] = 0
                calculated_balances[currency_id] -= cf.source_amount

            # При свапе целевую валюту НЕ добавляем на баланс (пользователь получает физически)

        elif cf.type == CashFlow.CashFlowType.BALANCE_EDIT.name:
            # Изменение баланса админом - устанавливаем точное значение
            if cf.target_currency:
                currency_id = str(cf.target_currency.id)
                # Для BALANCE_EDIT target_amount - это итоговый баланс после изменения
                calculated_balances[currency_id] = cf.target_amount

    # Убираем нулевые балансы
    calculated_balances = {k: v for k, v in calculated_balances.items() if abs(v) > 0.001}

    return calculated_balances


def recalculate_all_balances():
    """Пересчитывает балансы всех пользователей"""
    print("🔄 Начинаю пересчет балансов пользователей...")

    users: list[TgUser] = list(TgUser.objects.all())
    updated_count = 0
    discrepancies = []

    for user in users:
        # Рассчитываем баланс на основе CashFlow
        calculated_balances = calculate_balance_from_cashflow(user.id)

        # Сравниваем с текущим балансом
        current_balances = user.balances if user.balances else {}

        # Проверяем расхождения
        has_discrepancy = False
        discrepancy_details = []

        # Проверяем все валюты из calculated_balances
        for currency_id, calculated_amount in calculated_balances.items():
            current_amount = current_balances.get(currency_id, 0)
            if abs(calculated_amount - current_amount) > 0.01:
                has_discrepancy = True
                try:
                    currency = Currency.objects.get({"_id": int(currency_id)})
                    currency_symbol = currency.symbol
                except:
                    currency_symbol = f"ID:{currency_id}"

                discrepancy_details.append({
                    "currency": currency_symbol,
                    "current": current_amount,
                    "calculated": calculated_amount,
                    "difference": calculated_amount - current_amount
                })

        # Проверяем валюты, которые есть в текущем балансе, но нет в calculated
        for currency_id, current_amount in current_balances.items():
            if currency_id not in calculated_balances and abs(current_amount) > 0.01:
                has_discrepancy = True
                try:
                    currency = Currency.objects.get({"_id": int(currency_id)})
                    currency_symbol = currency.symbol
                except:
                    currency_symbol = f"ID:{currency_id}"

                discrepancy_details.append({
                    "currency": currency_symbol,
                    "current": current_amount,
                    "calculated": 0,
                    "difference": -current_amount
                })

        if has_discrepancy:
            discrepancies.append({
                "user_id": user.id,
                "username": user.username,
                "real_name": user.real_name,
                "details": discrepancy_details
            })

            # Обновляем баланс пользователя
            user.balances = calculated_balances
            user.save()
            updated_count += 1

            print(f"🔄 Обновлен баланс пользователя {user.id} (@{user.username})")
            for detail in discrepancy_details:
                print(f"   {detail['currency']}: {detail['current']} → {detail['calculated']} (разница: {detail['difference']:+.2f})")

    return updated_count, discrepancies


def generate_report(updated_count, discrepancies):
    """Генерирует отчет о миграции"""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    # Создаем папку для отчетов если её нет
    reports_dir = "migration_reports"
    if not os.path.exists(reports_dir):
        os.makedirs(reports_dir)

    report_file = os.path.join(reports_dir, f"balance_migration_report_{timestamp}.txt")

    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("ОТЧЕТ О МИГРАЦИИ БАЛАНСОВ И CASHFLOW\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"Дата и время: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Обновлено пользователей: {updated_count}\n")
        f.write(f"Найдено расхождений: {len(discrepancies)}\n\n")

        if discrepancies:
            f.write("ДЕТАЛИ РАСХОЖДЕНИЙ БАЛАНСОВ:\n")
            f.write("-" * 30 + "\n\n")

            for disc in discrepancies:
                f.write(f"Пользователь: {disc['user_id']} (@{disc['username']}) - {disc['real_name']}\n")
                for detail in disc['details']:
                    f.write(f"  {detail['currency']}: {detail['current']} → {detail['calculated']} (разница: {detail['difference']:+.2f})\n")
                f.write("\n")

    print(f"📄 Отчет создан: {report_file}")
    return report_file


def main():
    """Основная функция миграции"""
    ans = input('Введите ID пользователя для проверки или 0 для всех: ')
    if ans != '0':
        user_id = int(ans)
        balances = calculate_balance_from_cashflow(user_id)
        print(balances)
        return

    print("🚀 Начинаю миграцию исправления балансов и CashFlow...")
    print("⚠️  ВНИМАНИЕ: Эта операция изменит балансы пользователей и CashFlow записи!")
    print("💡 Убедитесь, что вы создали бэкап БД через CLI перед запуском!")

    # Запрашиваем подтверждение
    confirmation = input("\n❓ Продолжить миграцию? (введите 'YES' для подтверждения): ")
    if confirmation != "YES":
        print("❌ Миграция отменена пользователем")
        return

    # 2. Пересчитываем балансы пользователей
    updated_count, discrepancies = recalculate_all_balances()

    # 3. Генерируем отчет
    report_file = generate_report(updated_count, discrepancies)

    print(f"\n🎉 Миграция завершена!")
    print(f"📊 Статистика:")
    print(f"   Обновлено пользователей: {updated_count}")
    print(f"   Найдено расхождений: {len(discrepancies)}")
    print(f"   Отчет: {report_file}")

    if discrepancies:
        print(f"\n⚠️  Обнаружены расхождения у {len(discrepancies)} пользователей")
        print("📄 Подробности в отчете")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Миграция для добавления deal_id к существующим CashFlow записям
и обновления additional_data с информацией о направлении сделки
"""

from models.cash_flow import CashFlow
from models.deal import Deal
import os
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


def find_deal_for_cashflow(cf: CashFlow):
    """
    Находит сделку для CashFlow записи по параметрам:
    - owner (пользователь)
    - source_currency (исходная валюта)
    - target_currency (целевая валюта)
    - source_amount (сумма исходной валюты)
    - target_amount (сумма целевой валюты)
    """
    if cf.type != CashFlow.CashFlowType.SWAP.name:
        return None

    # Ищем сделки с подходящими параметрами
    potential_deals = Deal.objects.raw({
        "owner": cf.user.id,
        "source_currency": cf.source_currency.id,
        "target_currency": cf.target_currency.id,
        "status": Deal.DealStatuses.FINISHED.value
    })

    # Проверяем совпадение по суммам
    for deal in potential_deals:
        # Проверяем исходную сумму (может быть deal_value или original_deal_value)
        source_matches = (
            abs(deal.deal_value - cf.source_amount) < 0.01 or
            (deal.original_deal_value and abs(deal.original_deal_value - cf.source_amount) < 0.01)
        )

        # Проверяем целевую сумму
        target_matches = abs((deal.deal_value * deal.rate) - cf.target_amount) < 0.01

        if source_matches and target_matches:
            return deal

    return None


def migrate_cashflow():
    """Добавляет deal_id к существующим CashFlow и обновляет additional_data"""
    print("🔄 Начинаю миграцию CashFlow...")

    cashflows = list(CashFlow.objects.all())
    updated_count = 0
    linked_count = 0

    for cf in cashflows:
        updated = False

        # Добавляем deal_id если это SWAP и его еще нет
        if cf.type == CashFlow.CashFlowType.SWAP.name and (not hasattr(cf, 'deal_id') or cf.deal_id is None):
            deal = find_deal_for_cashflow(cf)
            if deal:
                cf.deal_id = deal.id
                linked_count += 1
                updated = True
                print(f"🔗 CashFlow #{cf.id} связан со сделкой #{deal.id}")

        # Обновляем additional_data если это старый формат "По курсу:"
        if cf.additional_data == "По курсу:" and hasattr(cf, 'deal_id') and cf.deal_id:
            try:
                deal = Deal.objects.get({"_id": cf.deal_id})
                cf.additional_data = f"По курсу({'Хочу получить' if deal.dir == 'wanna_receive' else 'Хочу отдать'}): "
                updated = True
                print(f"📝 Обновлен additional_data для CashFlow #{cf.id}")
            except:
                print(f"⚠️ Не найдена сделка #{cf.deal_id} для CashFlow #{cf.id}")

        if updated:
            cf.save()
            updated_count += 1

    print(f"\n🎉 Миграция завершена!")
    print(f"📊 Обновлено CashFlow записей: {updated_count}")
    print(f"🔗 Связано со сделками: {linked_count}")


if __name__ == "__main__":
    migrate_cashflow()

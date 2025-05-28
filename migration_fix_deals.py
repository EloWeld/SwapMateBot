#!/usr/bin/env python3
"""
Миграция для добавления original_deal_value к существующим сделкам
"""

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


def migrate_deals():
    """Добавляет original_deal_value к существующим сделкам"""
    print("🔄 Начинаю миграцию сделок...")

    deals = list(Deal.objects.all())
    updated_count = 0

    for deal in deals:
        if not hasattr(deal, 'original_deal_value') or deal.original_deal_value is None:
            deal.original_deal_value = deal.deal_value
            deal.save()
            updated_count += 1
            print(f"✅ Обновлена сделка #{deal.id}: original_deal_value = {deal.deal_value}")

    print(f"\n🎉 Миграция завершена! Обновлено сделок: {updated_count}")


if __name__ == "__main__":
    migrate_deals()

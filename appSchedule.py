from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv
import loguru
from models.tg_user import TgUser
from services.sheets_syncer import SheetsSyncer
import os
from os.path import join, dirname
from pymodm.connection import connect
from pymongo import MongoClient

# Load dotenv
dotenv_path = join(dirname(__file__), '.env')
load_dotenv()

# Loader constants
MONGODB_CONNECTION_URI = os.environ["MongoConnectionString"]
MONGO_DB_NAME = os.environ["MongoDatabaseName"]
BOT_TOKEN = os.environ["BotToken"]
REQUESTS_TIMEOUT = 8
MAX_INLINE_COUNT = 10

# Initialize MongoDB

MDB = MongoClient(MONGODB_CONNECTION_URI).get_database(MONGO_DB_NAME)
connect(MONGODB_CONNECTION_URI+f'/{MONGO_DB_NAME}?authSource=admin', alias="pymodm-conn")
# Выполнять функцию каждые 5 минут
SheetsSyncer.sync_currency_purchases()
SheetsSyncer.sync_deals()
SheetsSyncer.sync_currencies()
SheetsSyncer.sync_users_cash_flow()
loguru.logger.info("Synced")
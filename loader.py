from pymongo import MongoClient
import os
from os.path import join, dirname
from dotenv import load_dotenv
from loguru import logger

from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.types import ParseMode
from pymodm.connection import connect

# Load dotenc
dotenv_path = join(dirname(__file__), '.env')
load_dotenv()

# Loader constants
MONGODB_CONNECTION_URI = os.environ["MongoConnectionString"]
MONGO_DB_NAME = os.environ["MongoDatabaseName"]
BOT_TOKEN = os.environ["BotToken"]
REQUESTS_TIMEOUT = 8

# Initialize MongoDB

MDB = MongoClient(MONGODB_CONNECTION_URI).get_database(MONGO_DB_NAME)
connect(MONGODB_CONNECTION_URI+f'/{MONGO_DB_NAME}', alias="pymodm-conn")

# Constants class
class ConstantsMetaClass(type):
    def __getattr__(cls, key):
        doc = MDB.Settings.find_one(dict(id="Constants"))
        if not doc:
            MDB.Settings.insert_one(dict(id="Constants"))
            doc = MDB.Settings.find_one(dict(id="Constants"))
        # If key in constants
        if key in doc:
            return doc[key]

        raise AttributeError(key)

    def __str__(cls):
        return 'Const %s' % (cls.__name__,)


class Consts(metaclass=ConstantsMetaClass):
    pass


# Initialize Telegram bot
bot = Bot(BOT_TOKEN, parse_mode=ParseMode.HTML)
ms = MemoryStorage()
dp = Dispatcher(bot, storage=ms)
# Load middlewares
from middlewares.user_middleware import TgUserMiddleware
dp.setup_middleware(TgUserMiddleware())


async def onBotStartup(data):
    bot_info = await bot.get_me()
    
    MDB.Settings.update_one(dict(id="Constants"), {"$set": dict(BotUsername=bot_info.username)})
    from etc.utils import notifyAdmins
    logger.info(f"Bot started! https://t.me/{Consts.BotUsername}")
    await notifyAdmins(f"🤖 Запущен!")

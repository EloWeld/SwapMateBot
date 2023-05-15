
from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from loader import MDB

from models.tg_user import TgUser

class TgUserMiddleware(BaseMiddleware):
    async def on_pre_process_message(self, m: Message, data: dict):
        try:
            user: TgUser = TgUser.objects.get({"_id": m.from_user.id})
        except Exception as e:
            user = None
            return
        data['user'] = user
        
        return True
    
    async def on_pre_process_callback_query(self, c: CallbackQuery, data: dict):
        try:
            user: TgUser = TgUser.objects.get({"_id": c.from_user.id})
        except Exception as e:
            user = None
            return
        data['user'] = user
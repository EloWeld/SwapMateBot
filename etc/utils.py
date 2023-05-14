from typing import List
import loguru
from loader import MDB, bot
from models.tg_user import TgUser

async def notifyAdmins(text: str):
    admins: List[TgUser] = TgUser.objects.raw({"isAdmin": True})
    
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
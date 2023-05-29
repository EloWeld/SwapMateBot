from aiogram import types
from unittest.mock import AsyncMock, MagicMock

import pytest
from etc.keyboards import Keyboards

from handlers.start import start_cmd
from models.tg_user import TgUser

@pytest.mark.asyncio
async def test_start_handler():
    message = MagicMock(spec=types.Message)
    message.from_user.id = 2706441611536
    await start_cmd(message, None)

    test_user = TgUser(2706441611536, is_admin=False)

    message.answer.assert_called_with('🚀 Добро пожаловать в бота! Для продолжения заполните заявку. Пока что вам доступен ограниченный функционал', reply_markup=Keyboards.Identify.start_identify())


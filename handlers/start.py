from etc.keyboards import Keyboards
from loader import dp
from aiogram.types import Message, CallbackQuery
from models.tg_user import TgUser
from aiogram.dispatcher import FSMContext

@dp.message_handler(commands="start", state="*")
async def _(m:Message, state:FSMContext=None):
    
    
    try:
        user = TgUser.objects.get({'_id': m.from_user.id})
    except TgUser.DoesNotExist:
        user = TgUser(m.from_user.id)

    # User exists already
    user.fullname = m.from_user.full_name
    user.username = m.from_user.username
    user.save()
    
    await m.answer("Hello!", reply_markup=Keyboards.start_menu(user))
    


@dp.callback_query_handler(lambda c: c.data.startswith('|main'), state="*")
async def _(c: CallbackQuery, state: FSMContext=None, user: TgUser = None):
    
    await c.message.edit_text("Hello!", reply_markup=Keyboards.start_menu(user))
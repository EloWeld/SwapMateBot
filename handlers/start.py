from etc.keyboards import Keyboards
from loader import bot, dp
from aiogram.types import Message, CallbackQuery, BotCommand, BotCommandScopeAllPrivateChats
from models.tg_user import TgUser
from aiogram.dispatcher import FSMContext

@dp.message_handler(commands="start", state="*")
async def start_cmd(m:Message, state:FSMContext=None):
    if state:
        await state.finish()
    try:
        user = TgUser.objects.get({'_id': m.from_user.id})
    except TgUser.DoesNotExist:
        user = TgUser(m.from_user.id)

    # User exists already
    user.fullname = m.from_user.full_name
    user.username = m.from_user.username
    user.save()

    if user.is_member:
        await m.answer("💠 Главное меню 💠", reply_markup=Keyboards.start_menu(user))
        await bot.set_my_commands([
            BotCommand("start", "Перезапуск бота")
        ], scope=BotCommandScopeAllPrivateChats())
    else:
        if user.join_request_status == "SENT":
             await m.answer("🚀 Добро пожаловать в бота! Ожидайте рассмотрения заявки...")
        elif user.join_request_status == "DISCARDED":
             await m.answer("🚀 Добро пожаловать в бота! Ожидайте рассмотрения заявки...")
        else:
            await m.answer("🚀 Добро пожаловать в бота! Для продолжения заполните заявку. Пока что вам доступен ограниченный функционал", reply_markup=Keyboards.Identify.start_identify())
    


@dp.callback_query_handler(lambda c: c.data.startswith('|main'), state="*")
async def _(c: CallbackQuery, state: FSMContext=None, user: TgUser = None):
    if state:
            await state.finish()
    await c.message.edit_text("Hello!", reply_markup=Keyboards.start_menu(user))
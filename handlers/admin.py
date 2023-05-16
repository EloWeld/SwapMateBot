from typing import List
from etc.utils import get_rates_text
from loader import dp
from aiogram.types import CallbackQuery, Message, ContentType
from aiogram.dispatcher.filters import ContentTypeFilter
from aiogram.dispatcher import FSMContext
from models.deal import Deal
from models.etc import Currency
from models.tg_user import TgUser
from etc.keyboards import Keyboards


@dp.callback_query_handler(lambda c: c.data.startswith('|admin'), state="*")
async def _(c: CallbackQuery, state: FSMContext=None, user: TgUser = None):
    actions = c.data.split(':')[1:]
    
    
    if actions[0] == "main":
        await c.message.edit_text("Админ меню", reply_markup=Keyboards.admin_menu(user))
        return
    
    if actions[0] == "setup_exchange_rates":
        currencies: List[Currency] = Currency.objects.raw({"is_available": True})
        await c.message.edit_text("💎 Выберите валюту чтобы установить её курс\n\nТекущие курсы:\n" + get_rates_text(), 
                                  reply_markup=Keyboards.Admin.choose_currency_to_change_rate(currencies))
        
    if actions[0] == "my_deals":
        deals = Deal.objects.all()
        await c.message.edit_text("💎 Выберите тип сделок", reply_markup=Keyboards.Admin.dealsTypes(deals))
        
    if actions[0] == "deals_with_status":
        status = actions[1]
        verbose_status = {'CANCELLED': 'Отменённая', 'ACTIVE': 'Активная', 'FINISHED': 'Завершённая'}[status]
        deals = Deal.objects.raw({"status": status})
        await c.message.edit_text(f"💎 Ниже список сделок со статусом {verbose_status}", reply_markup=Keyboards.Admin.deals(deals))
        
    
    if actions[0] == "finish_deal":
        deals = Deal.objects.all()
        await c.message.edit_text("В разработке", reply_markup=Keyboards.back('|main'))
    if actions[0] == "cancel_deal":
        deals = Deal.objects.all()
        await c.message.edit_text("В разработке", reply_markup=Keyboards.back('|main'))
        
    if actions[0] == "send_deal_receipt":
        await c.message.edit_text("🧾 Приложите чек для отправки", reply_markup=Keyboards.back('|main'))
        await state.set_state("send_receipt")
        



@dp.message_handler(content_types=[ContentType.PHOTO], state="send_receipt")
async def _(m: Message, state: FSMContext = None):
    await m.answer("Чек не отправлен потому что вы дурак")
import datetime
import random
from typing import List, Union
from etc.keyboards import Keyboards
from etc.states import UserStates
from etc.texts import BOT_TEXTS
from etc.utils import get_rates_text, notifyAdmins
from handlers.deal import get_calc_text
from loader import dp
from aiogram.types import CallbackQuery, Message
from aiogram.dispatcher import FSMContext
from models.deal import Deal
from models.etc import Currency
from models.tg_user import TgUser
import requests

@dp.callback_query_handler(lambda c: c.data.startswith('|convertor:'), state="*")
async def _(c: CallbackQuery, state: FSMContext=None, user: TgUser = None):
    actions = c.data.split(':')[1:]
    stateData = {} if state is None else await state.get_data()
    
    if actions[0] == "deals_history":
        deals = Deal.objects.raw({"owner": user.id})
        if not deals:
            await c.answer("🕸️ Ваша история свапов пуста", show_alert=True)
            return
        
        await c.message.edit_text("📊 Ваша история свапов:", reply_markup=Keyboards.Deals.user_deals_history(deals))
    if actions[0] == "actual_rates":
        if state:
            await state.finish()
        is_demo = actions[-1] == "demo"
        await c.message.edit_text("⭐ Актуальные курсы валют ниже\n\n"
                                  + get_rates_text(is_demo), reply_markup=Keyboards.actual_rates() if not is_demo else Keyboards.hide())
    if actions[0] == "deal_calc":
        await state.finish()
        stateData = {}
        await c.message.edit_text(get_calc_text(user), 
                                  reply_markup=Keyboards.Calc.main(user, stateData.get('sel_from', None), stateData.get('sel_to', None)))
    if actions[0] == "see_deal":
        try:
            deal: Deal = Deal.objects.get({"_id": int(actions[1])})
        except Deal.DoesNotExist as e:
            await c.answer(f"❌ Свап #{actions[1]} не найден", show_alert=True)
            return
        
        await c.message.edit_text(deal.get_user_text(), reply_markup=Keyboards.Deals.deal_info(user, deal))
        
    if actions[0] == "found_cheaper":
        await c.answer()
        await c.message.edit_text("🛒 Нашли дешевле?\n🎁 Мы предложим цену ещё лучше. \n⚠️ Закрепи фото или ссылку .\n", 
                               reply_markup=Keyboards.back('|convertor:actual_rates'))
        await UserStates.FindCheaper.set()
from loader import bot
from aiogram.types import ContentType
@dp.message_handler(state=UserStates.FindCheaper, content_types=[ContentType.TEXT, ContentType.PHOTO])
async def _(m: Message, state: FSMContext, user: TgUser = None):
    stateData = await state.get_data()
    await state.finish()
    
    text = f"Покупатель <a href='tg://user?id={user.id}'>{user.real_name}</a> нашёл курсы выгоднее!\n" \
           f"\n" \
           f"👤 Комментарий пользователя: <b>{m.text if m.text else m.caption if m.caption else '➖'}</b>"
    admins: List[TgUser] = TgUser.objects.raw({"is_admin": True})
    for admin in admins:
        if len(m.photo) > 0:
            await bot.send_photo(admin.id, m.photo[0].file_id, caption=text)
        else:
            await bot.send_message(admin,id, text)
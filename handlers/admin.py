from loader import dp
from aiogram.types import CallbackQuery, Message
from aiogram.dispatcher import FSMContext
from models.deal import Deal
from models.tg_user import TgUser
from etc.keyboards import Keyboards


@dp.callback_query_handler(lambda c: c.data.startswith('|admin'), state="*")
async def _(c: CallbackQuery, state: FSMContext=None, user: TgUser = None):
    actions = c.data.split(':')[1:]
    
    
    if actions[0] == "main":
        await c.message.edit_text("Админ меню", reply_markup=Keyboards.admin_menu(user))
        return
    
    if actions[0] == "my_deals":
        deals = Deal.objects.all()
        await c.message.edit_text("💎 Выберите тип сделок", reply_markup=Keyboards.Admin.dealsTypes(deals))
        
    if actions[0] == "deals_with_status":
        status = actions[1]
        verbose_status = {'CANCELLED': 'Отменённая', 'ACTIVE': 'Активная', 'FINISHED': 'Завершённая'}[status]
        deals = Deal.objects.raw({"status": status})
        await c.message.edit_text(f"💎 Ниже список сделок со статусом {verbose_status}", reply_markup=Keyboards.Admin.deals(deals))
        
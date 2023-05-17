from aiogram.dispatcher.filters.state import State, StatesGroup

class AdminInputStates(StatesGroup):
    SendReceipt = State()
    ChangeRate = State()
    BuyCurrency = State()
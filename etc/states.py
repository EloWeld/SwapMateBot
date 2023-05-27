from aiogram.dispatcher.filters.state import State, StatesGroup

class AdminInputStates(StatesGroup):
    SendReceipt = State()
    ChangeRate = State()
    BuyCurrencyTargetAmount = State()
    BuyCurrencySourceType = State()
    BuyCurrencySourceAmount = State()
    ChangeUserBalance = State()

class IdentifyState(StatesGroup):
    Name = State()
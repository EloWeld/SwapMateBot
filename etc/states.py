from aiogram.dispatcher.filters.state import State, StatesGroup

class AdminInputStates(StatesGroup):
    BroadcastData = State()
    BroadcastLinks = State()
    SendReceipt = State()
    ChangeRate = State()
    BuyCurrencyAmounts = State()
    ChangeUserBalance = State()
    ChangeDealRate = State()
    ChangeUserRealName = State()

class IdentifyState(StatesGroup):
    Name = State()

class UserStates(StatesGroup):
    SuggestRate = State()
    FindCheaper = State()
    RefillBalance = State()
    DealAdditionalInfo = State()

class DealStates(StatesGroup):
    Value = State()
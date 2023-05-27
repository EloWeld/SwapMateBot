from pydantic import BaseModel
import json

class BotTexts(BaseModel):
    AdminMenuBtn = "🛡️ Админка 🛡️"
    SetExchangeRates = "🔄 Установить курсы"
    MyCurrencies = "💰 Мои валюты"
    MyDeals = "🤝 Мои свапы"
    MyRates = "📈 Мои курсы"
    MyUsers = "👥 Пользователи"
    Profile = "👩🏻‍💻 Профиль"
    
    
    DealCalc = "📊 Калькулятор свапов"
    DealsHistory = "🗄 История свапов"
    ActualRates = "⭐️ Актуальные курсы"
    
    BackButton = "🔙 Назад"
    Continue = "🏁 Продолжить"
    Previous = "⬅"
    Next = "➡"
    
    InvalidValue = "❗ Некорректное значение"
    
    SendDeal = "✅ Отправить"
    Cancel="❌ Отменить"
    
    SendReceipt = "🧾 ОТПРАВИТЬ ЧЕК"
    Finish = "🏁 Завершить"
    FoundCheaper = "📈 Нашёл дешевле!"

    verbose_emoji = {
        "CANCELLED": "⛔", 
        "ACTIVE": "⏳", 
        "FINISHED": "🏁"
    }

    verbose = {
        True: "Да",
        False: "Нет",
        "CANCELLED": "Отменённая", 
        "ACTIVE": "Активная", 
        "FINISHED": "Завершённая"
    }

# Создаем экземпляр класса
BOT_TEXTS = BotTexts()

# Сериализация в JSON
bot_texts_json = BOT_TEXTS.json(ensure_ascii=False)

# Записываем JSON в файл
with open('src/bot_texts.json', 'w', encoding='utf-8') as file:
    file.write(bot_texts_json)

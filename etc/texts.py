from pydantic import BaseModel
import json

class BotTexts(BaseModel):
    AdminMenuBtn = "💠 Админка 💠"
    SetExchangeRates = "🔄 Установить курсы"
    MyCurrencies = "💰 Мои валюты"
    MyDeals = "🤝 Мои свапы"
    MyRates = "📈 Мои курсы"
    
    
    DealCalc = "📊 Калькулятор свапов"
    DealsHistory = "🗄 История сделок"
    ActualRates = "⭐️ Актуальные курсы"
    
    BackButton = "🔙 Назад"
    Continue = "🏁 Продолжить"
    
    InvalidValue = "❗ Некорректное значение"
    
    SendDeal = "✅ Отправить"
    Cancel="❌ Отменить"
    
    SendReceipt = "🧾 ОТПРАВИТЬ ЧЕК"
    Finish = "🏁 Завершить"
    FoundCheaper = "📈 Нашёл дешевле!"

# Создаем экземпляр класса
BOT_TEXTS = BotTexts()

# Сериализация в JSON
bot_texts_json = BOT_TEXTS.json(ensure_ascii=False)

# Записываем JSON в файл
with open('src/bot_texts.json', 'w', encoding='utf-8') as file:
    file.write(bot_texts_json)

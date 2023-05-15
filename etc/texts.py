from pydantic import BaseModel
import json

class BotTexts(BaseModel):
    AdminMenuBtn = "💠 Админка 💠"
    SetExchangeRates = "🔄 Установить курсы валют"
    MyCurrencies = "💰 Мои валюты"
    MyDeals = "🤝 Мои сделки"
    MyRates = "📈 Мои курсы"
    
    
    DealCalc = "📊 Калькулятор сделки"
    DealsHistory = "🗄 История сделок"
    ActualRates = "⭐️ Актуальные курсы валют"
    
    BackButton = "⬅️ Назад"
    Continue = "🏁 Продолжить"

# Создаем экземпляр класса
BOT_TEXTS = BotTexts()

# Сериализация в JSON
bot_texts_json = BOT_TEXTS.json(ensure_ascii=False)

# Записываем JSON в файл
with open('src/bot_texts.json', 'w', encoding='utf-8') as file:
    file.write(bot_texts_json)

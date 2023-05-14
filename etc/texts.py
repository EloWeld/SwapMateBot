from pydantic import BaseModel
import json

class BotTexts(BaseModel):
    AdminMenuBtn: str = "💠 Админка 💠"
    DealCalc: str = "📊 Калькулятор сделки"
    DealsHistory: str = "🗄 История сделок"
    ActualRates: str = "⭐️ Актуальные курсы валют"

# Создаем экземпляр класса
BOT_TEXTS = BotTexts()

# Сериализация в JSON
bot_texts_json = BOT_TEXTS.json()

# Записываем JSON в файл
with open('src/bot_texts.json', 'w') as file:
    file.write(bot_texts_json)

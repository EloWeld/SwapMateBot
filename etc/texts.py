from pydantic import BaseModel
import json


class BotTexts(BaseModel):
    AdminMenuBtn = "🛡️ Админка 🛡️"
    SetExchangeRates = "🔄 Установить курсы"
    MyCurrencies = "💰 Купить валюту"
    MyDeals = "🤝 Мои свапы"
    MyRates = "📈 Мои курсы"
    MyUsers = "👥 Пользователи"
    Broadcast = "📢 Рассылка"
    Profile = "👩🏻‍💻 Профиль"

    DealCalc = "📊 ДАЮ-ПОЛУЧАЮ"
    DealsHistory = "🗄 История свапов"
    ActualRates = "⭐️ Актуальные курсы"

    BackButton = "🔙 Назад"
    Continue = "🏁 Продолжить"
    Previous = "⬅"
    Next = "➡"
    Buy = "➡️💸➡️"
    RefillBalance = "📥 Пополнить баланс"
    RefillsHistory = "🗃️ История пополнений"
    ChangeDealRate = "✒️ Изменить курс сделки"
    AnullateDeal = "❌ Анулировать сделку"

    InvalidValue = "❗ Некорректное значение"

    Hide = "➖➖➖Скрыть➖➖➖"
    SendDeal = "✅ Отправить"
    # BuyCurrency = "💸 Купить валюту себе как Админ 💸"
    Cancel = "❌ Отменить"
    AddInfo = "📝 Добавить доп. информацию"
    ChangeAddInfo = "📝 Изменить доп. информацию"

    SendReceipt = "🧾 ОТПРАВИТЬ ЧЕК"
    Finish = "🏁 Завершить"
    FoundCheaper = "📈 Нашёл дешевле!"

    SuggestRate = "💡 Предложить курс"
    OpenUser = "👤 Открыть профиль пользователя"
    
    ChangeDealDir = "🖋️ Изменить"
    
    RefillsChat = "📥 Чат пополнений"
    MainMenuButton = "🏠 На главную"
    LearningVideos = "📽️ Обучающие видео"
    Exit = "🚪 Выход"

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

    MainMenuText = "💠 Главное меню 💠"


# Создаем экземпляр класса
BOT_TEXTS = BotTexts()

# Сериализация в JSON
bot_texts_json = BOT_TEXTS.json(ensure_ascii=False)

# Записываем JSON в файл
with open('src/bot_texts.json', 'w', encoding='utf-8') as file:
    file.write(bot_texts_json)

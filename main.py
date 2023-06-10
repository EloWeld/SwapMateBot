from aiogram.utils import executor
from loader import *

from handlers import *
from loguru import logger


def main():
    # Добавляем обработчик для записи логов в файл
    logger.add("botlog.log")
    executor.start_polling(dp, on_startup=onBotStartup)


if __name__ == "__main__":
    main()

from aiogram.utils import executor
from loader import *

from handlers import *


def main():
    executor.start_polling(dp, on_startup=onBotStartup)


if __name__ == "__main__":
    main()

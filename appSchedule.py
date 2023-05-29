from loader import *
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import loguru
from models.tg_user import TgUser
from services.sheets_syncer import SheetsSyncer


def scheduled_sync():
    # Выполнять функцию каждые 5 минут
    for owner in TgUser.objects.raw({"is_admin": True}):
        SheetsSyncer.sync_currency_purchases(owner)
        SheetsSyncer.sync_deals(owner)
        loguru.logger.info("Synced")


def main():
    scheduler = AsyncIOScheduler()
    scheduler.add_job(scheduled_sync, "interval", minutes=5)  # Планирование выполнения функции каждые 5 минут
    scheduled_sync()
    scheduler.start()


if __name__ == "__main__":
    main()
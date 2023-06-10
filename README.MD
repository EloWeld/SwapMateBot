### Swap Mate Bot

# Telegram bot

Used libs: Pydantic, PymoMM, Pymongo, Aiogram, Loguru, Python-dotenv etc.

Add cron task to sync with tables:
```
crontab -e
*/5 * * * * cd /path_to_project_folder/ && /path_to_project_folder/venv/bin/python3 /path_to_project_folder/main.py >> /path_to_project_folder/schedule.log 2>&1
```
import subprocess
import sys


if __name__ == "__main__":
    BotMain = subprocess.Popen([sys.executable, "appBot.py"], shell=False)
    Scheduler = subprocess.Popen(
        [sys.executable, "appSchedule.py"], shell=False)
    BotMain.communicate()
    Scheduler.communicate()

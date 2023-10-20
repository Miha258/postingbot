from aiogram import Bot
import os, sys
from aiogram.contrib.fsm_storage.memory import MemoryStorage


bot_token = sys.argv[1]
bot = Bot(token = bot_token)
owner = sys.argv[2]
bot_type = sys.argv[3]
storage = MemoryStorage()

def get_channel():
    return os.environ.get("TARGET_CHANNEL")

def set_channel(channel):
    os.environ["TARGET_CHANNEL"] = channel
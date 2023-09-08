from aiogram import Bot
import sys, os
from aiogram.contrib.fsm_storage.memory import MemoryStorage


bot_token = "5170217792:AAEROxDDKYsGkfu9t4Ck0clU2UsVjbuO0YQ"
bot = Bot(token = bot_token)
owner = "1095610815"
bot_type = "inviting"
storage = MemoryStorage()

def get_channel():
    return os.environ.get("TARGET_CHANNEL")

def set_channel(channel):
    os.environ["TARGET_CHANNEL"] = channel

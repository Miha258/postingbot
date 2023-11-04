from aiogram import Bot
import os
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.types import ParseMode

bot_token = "5323882359:AAFIUxLGcdgiEzEsYShmI6CwI9FvX1oKZOc"
bot = Bot(token = bot_token, parse_mode = ParseMode.HTML)
owner = "1095610815"
bot_type = "inviting"
storage = MemoryStorage()

def get_channel():
    return os.environ.get("TARGET_CHANNEL")

def set_channel(channel):
    os.environ["TARGET_CHANNEL"] = channel
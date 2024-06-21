from aiogram import Bot
import os, sys
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.types import ParseMode

bot_token = sys.argv[1]
bot = Bot(token = bot_token, parse_mode = ParseMode.HTML)
owner = sys.argv[2]
bot_type = sys.argv[3]
storage = MemoryStorage()

channels = {}
def get_channel(user_id):
    return channels.get(user_id)

def set_channel(user_id, channel):
    channels[user_id] = channel
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
import aiohttp
from db.account import Admins
from aiogram.dispatcher.filters import BoundFilter
from create_bot import owner, get_channel, bot, channels
import re
import datetime

def get_button_by_callback_data(callback_query: str, keyboard: InlineKeyboardMarkup) -> InlineKeyboardButton:
    for row in keyboard.inline_keyboard:
        for button in row:
            if button.callback_data == callback_query:
                return button

def remove_button_by_callback_data(callback_query: str, keyboard: InlineKeyboardMarkup):
    for row in keyboard.inline_keyboard:
        for button in row:
            if button.callback_data == callback_query:
                row.remove(button)

async def fetch_media_bytes(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            image_bytes = await response.read()
            return image_bytes 
        

class IsAdminFilter(BoundFilter):
    async def check(self, message: Message) -> bool:
        admins = await Admins.get('bot_id', bot.id, True)
        if admins:
            return message.from_user.id == int(owner) or [admin["id"] for admin in admins]
        else:
            return message.from_user.id == int(owner)
    

class IsOwnerFilter(BoundFilter):
    async def check(self, message: Message) -> bool:
        return message.from_user.id == int(owner)


class IsChannel(BoundFilter):
    async def check(self, message: Message) -> bool:
        if get_channel(message.from_id):
            return True
        else:
            await message.answer('Ви не вибрали канал, скористайтеся меню, щоб це зробити:')
            return False


def parse_date(date_str: str, date: datetime.datetime = None):
    try:
        regex_patterns = [
            r'(\d{1,2})[:\s](\d{1,2}) (\d{1,2}) (\d{1,2}) (\d{4})',
            r'(\d{1,2})[:\s](\d{1,2})\.(?:\d{1,2})\.(\d{4})',
            r'(\d{1,2})[:\s](\d{1,2}) (\d{1,2}) (\d{1,2})',
            r'(\d{1,2})[:\s](\d{1,2}) (\d{1,2})',
            r'(\d{1,2})[:\s](\d{1,2})',
        ]
        current_date = None
        for i, pattern in enumerate(regex_patterns):
            match = re.match(pattern, date_str)
            if match:
                groups = match.groups()
                if date_str.count('.') == 1:
                    current_date = datetime.datetime.strptime(date_str, '%H:%M %d.%m').replace(year = datetime.datetime.now().year) if ':' in date_str else datetime.datetime.strptime(date_str, '%H %M %d.%m').replace(year = datetime.datetime.now().year)
                elif date_str.count('.') == 2:
                    current_date = datetime.datetime.strptime(date_str, '%H:%M %d.%m.%Y') if ':' in date_str else datetime.datetime.strptime(date_str, '%H %M %d.%m.%Y')
                elif i == 0: 
                    current_date = datetime.datetime.strptime(date_str, '%H:%M %d %m %Y') if ':' in date_str else datetime.datetime.strptime(date_str, '%H %M %d %m %Y')
                elif i == 2:
                    current_date = datetime.datetime.now().replace(hour=int(groups[0]), minute=int(groups[1]), day=int(groups[2]), month=int(groups[3]), second = 0, microsecond = 0)
                    if date:
                        current_date = current_date.replace(year = date.year)
                elif i == 3:
                    current_date = datetime.datetime.now().replace(hour=int(groups[0]), minute=int(groups[1]), day=int(groups[2]), second = 0, microsecond = 0)
                    if date:
                        current_date = current_date.replace(month = date.month, year = date.year)
                elif i == 4:
                    current_date = datetime.datetime.now().replace(hour=int(groups[0]), minute=int(groups[1]), second = 0, microsecond = 0)
                    if date:
                        current_date = current_date.replace(day = date.day, month = date.month, year = date.year)
        return current_date
    except ValueError:
        return

find_media_type = lambda string: [t for t in ('photos', 'videos', 'animations') if t in string][0]

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
import aiohttp
from aiogram.dispatcher.filters import BoundFilter
from create_bot import owner

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
        

def is_photo(file):
    file_name = file.get_file_name()
    image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp']
    return any(file_name.lower().endswith(ext) for ext in image_extensions)

def is_video(file):
    file_name = file.get_file_name()
    video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.wmv']
    return any(file_name.lower().endswith(ext) for ext in video_extensions)


class IsAdminFilter(BoundFilter):
    async def check(self, message: Message) -> bool:
        return message.from_user.id == int(owner)
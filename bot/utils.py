from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import aiohttp

def get_button_by_callback_data(callback_query: str, keyboard: InlineKeyboardMarkup) -> InlineKeyboardButton:
    for row in keyboard.inline_keyboard:
        for button in row:
            if button.callback_data == callback_query:
                return button
    return None

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
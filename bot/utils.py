from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
import aiohttp
from aiogram.dispatcher.filters import BoundFilter
from create_bot import owner, get_channel
from moviepy.editor import VideoFileClip
from os import remove as del_file
from imgurpython import ImgurClient

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
        return message.from_user.id == int(owner)
    
class IsChannel(BoundFilter):
    async def check(self, message: Message) -> bool:
        if get_channel():
            return True
        else:
            await message.answer('Ви не вибрали канал, скористайтеся меню, щоб це зробити:')
            return False


client_id = 'bff5bece377f4eb'
client_secret = '266bafe614f0a7e53b170ed13ad24bdb25ccff9c'
client = ImgurClient(client_id, client_secret)
def convert_video_to_gif(file: bytes):
    with open('video.mp4', 'wb') as f:
        f.write(file)

    clip = VideoFileClip('video.mp4')
    clip.write_gif('out.gif', fps = 20)
    del_file('video.mp4')
    # image = client.upload_from_path('out.gif', config=None, anon=True)
    # del_file('out.gif')
    # return image['link']

# import asyncio
# async def main():
#     file = await fetch_media_bytes()
#     print(convert_video_to_gif(file))

# asyncio.run(main())
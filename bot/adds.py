from aiogram import types, Dispatcher
from states import BotAdds
from aiogram.dispatcher import FSMContext
from db.account import Users
from keyboards import *
from create_bot import bot
import re

async def ask_media(message: types.Message, state: FSMContext):
    await message.answer("Надішліть текст, фото/відео:", reply_markup = back_to_menu())
    await state.set_state(BotAdds.MEDIA)


async def skip_btn(message: types.Message, state: FSMContext):
    await check_adds(message, state)


async def ask_for_btn(message: types.Message, state: FSMContext):
    await state.update_data({'text': message.caption or message.text, 'media': message.photo[-1] if message.photo else message.video})
    await state.set_state(BotAdds.BTN)
    await message.reply("Введіть кнопку у форматі: \n<em>1. Кнопка - посилання</em>\n<em>2. Кнопка - посилання</em>\n<em>3. Кнопка - посилання</em>", reply_markup = skip_menu(), parse_mode = "html")


async def check_adds(message: types.Message, state: FSMContext):
    regex_pattern = r'([^\-]+) - ([^\n]+)'

    matches = re.findall(regex_pattern, message.text)
    kb = None
    if matches:
        kb = types.InlineKeyboardMarkup(row_width = 1)

        for name, link in matches:
            button = types.InlineKeyboardButton(text = name, url = link)
            kb.add(button)
    
    await state.update_data({'kb': kb})
   
    async with state.proxy() as data:
        text = data.get("text")
        media = data.get("media")
        kb = data.get("kb")

    if media:
        if isinstance(media, types.PhotoSize):
            await message.answer_photo(media.file_id, text, reply_markup = kb)
        elif isinstance(media, types.Video):
            await message.answer_video(media.file_id, text, reply_markup = kb)
    else:
        await message.answer(text, reply_markup = kb)

    await message.answer("Зараз ваше оголошення виглядає так:", reply_markup = check_add_menu())
    await state.set_state(BotAdds.CHECK)


async def send_adds_to_users(message: types.Message, state: FSMContext):
    users = await Users.get('bot_id', bot.id, True)
    async with state.proxy() as data:
        text = data.get("text")
        media = data.get("media")
        kb = data.get("kb")
    
        if users:
            counter = 0
            for user in users:
                try:
                    channel = user['id']
                    if media:
                        if isinstance(media, types.PhotoSize):
                            await bot.send_photo(channel, media.file_id, text, reply_markup = kb)
                        elif isinstance(media, types.Video):
                            await bot.send_video(channel, media.file_id, text, reply_markup = kb)
                    else:
                        await bot.send_message(channel, text, reply_markup = kb)
                    counter += 1
                except:
                    pass
            await message.answer(f"Розсилка відбулася успішно.Кількість надсилань: <b>{counter}</b>", reply_markup = main_menu(), parse_mode = "html")
        else:
            await message.answer(f"База даних бота пуста.Спробуйте пізніше", reply_markup = main_menu())
    await state.finish()


def register_adds(dp: Dispatcher):
    dp.register_message_handler(ask_media, lambda m: m.text == "Розсилка", state = "*")
    dp.register_message_handler(ask_media, lambda m: m.text == "Редагувати", state = BotAdds.CHECK)
    dp.register_message_handler(skip_btn, lambda m: m.text == "Пропустити", state = BotAdds.BTN)
    dp.register_message_handler(ask_for_btn, state = BotAdds.MEDIA, content_types = types.ContentTypes.PHOTO | types.ContentTypes.VIDEO | types.ContentTypes.TEXT)
    dp.register_message_handler(check_adds, state = BotAdds.BTN, content_types = types.ContentTypes.TEXT)
    dp.register_message_handler(send_adds_to_users, lambda m: m.text == "Опублікувати", state = BotAdds.CHECK)
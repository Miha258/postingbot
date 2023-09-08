from aiogram import types
from aiogram.dispatcher import Dispatcher
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton, ReplyKeyboardMarkup
from aiogram.dispatcher import FSMContext
from states import BotStates
from utils import *
from create_bot import bot, get_channel , storage
import random
import asyncio
from db.account import Bots, Users
from chatgpt import *
channels = {}

options = {
    '🔡Капча': "bot_checking", 
    "🤖ChatGPT": "chatgpt",
    "📑Установити текст": "set_greet_text"
}
channels = {}

kb = InlineKeyboardMarkup(inline_keyboard = [
    [InlineKeyboardButton(name, callback_data = data)] for name, data in list(options.items())
])


async def greet_menu(message: types.Message):
    channel = get_channel()
    if channels.get(channel):
        greeting_message = channels[channel]["greeting_message"]
    else:
        greeting_message = "немає"
        channels[channel] = {
            "greeting_message": greeting_message,
            "type": "off"
        }
    await message.answer(f'Текст в привітанні: <b>{greeting_message}</b>.\n\nВиберіть опцію:', reply_markup = kb, parse_mode = 'html')

async def option_handler(callback_query: types.CallbackQuery, state: FSMContext):
    bot = await Bots.get("id", callback_query.message.from_id)

    if bot:
        if callback_query.data == "chatgpt" and not bot["subscription"]:
            return await callback_query.answer("Ця функці доступна лише після покупки тарифу", show_alert = True)

    channel = get_channel()
    if not channels.get(channel):
        channels[channel] = {"type": "off"}
    
    if channels[channel]["type"] == "off": 
        channels[channel]["type"] = callback_query.data
        button = get_button_by_callback_data(channels[channel]["type"], kb)
        button.text = "🔹" + button.text
        if callback_query.data == "set_greet_text":
            await callback_query.message.answer("Ввдедіть текст:")
            await state.set_state(BotStates.SET_GREED_TEXT)
    else:
        button = get_button_by_callback_data(channels[channel]["type"], kb)
        button.text = button.text.removeprefix("🔹")
        
        channels[channel]["type"] = callback_query.data
        button = get_button_by_callback_data(channels[channel]["type"], kb)
        button.text = "🔹" + button.text
        if callback_query.data == "set_greet_text":
            await callback_query.message.answer("Ввдедіть текст:")
            await state.set_state(BotStates.SET_GREED_TEXT)


    greeting_message = channels[channel]["greeting_message"]
    await callback_query.message.edit_text(f'Текст в привітанні: <b>{greeting_message}</b>.\n\nВиберіть опцію:', reply_markup = kb, parse_mode = 'html')


async def bot_checking(request: types.ChatJoinRequest):
    await bot.send_message(request.user_chat_id, f"Підтвердіть, що ви <b>не робот</b>:", reply_markup = ReplyKeyboardMarkup(keyboard = [[KeyboardButton("Я не робот 🟢"), KeyboardButton("Відмовитись 🔴")]], resize_keyboard = True),parse_mode = "html")
    await storage.set_state(chat = request.user_chat_id, state = BotStates.BOT_CHECKING)
    await asyncio.sleep(1024)
    await request.approve()

async def chat_gpt(request: types.ChatJoinRequest):
    await bot.send_message(request.user_chat_id, f"Привіт! Я вас слухаю. Що ви б хотіли обговорити чи запитати?", parse_mode = "html")
    await storage.set_state(chat = request.user_chat_id, state = BotStates.CHAT_GPT)

async def chat_gpt_answer(message: types.Message):
    if not Users.get('id', message.from_id):
        await Users(message.from_id, bot_id = bot.id)()
    answer = await enter_question(message.from_id, message.text)
    await message.answer(answer, parse_mode = "html")

async def check_season(message: types.Message, state: FSMContext):
    if not await Users.get('id', message.from_id):
        await Users(message.from_id, bot_id = bot.id)()

    if message.text in "Я не робот 🟢":
        await message.reply(f"Перевірку <b>пройдено!</b>", parse_mode = "html")
        return await state.finish()

    await message.reply("Ви відмовились від перевірки.")  


async def set_greet_text(message: types.Message, state: FSMContext):
    greeting_message = message.text
    channel = get_channel()
    channels[channel]["greeting_message"] = greeting_message
    
    await greet_menu(message)
    await state.finish()


async def greeting_request_handler(request: types.ChatJoinRequest):
    channel = channels.get(str(request.chat.id))
    if channel:
        request_type = channel["type"]
        if request_type != "off":
            match request_type:
                case "bot_checking":
                    await bot_checking(request)
                case "chatgpt":
                    await chat_gpt(request)
                case "set_greet_text":
                    greeting_message = channel["greeting_message"]
                    await bot.send_message(request.from_user.id, greeting_message, parse_mode = "html")


def register_greet(dp: Dispatcher):
    dp.register_callback_query_handler(option_handler, lambda query: query.data in options.values())
    dp.register_message_handler(check_season, state = BotStates.BOT_CHECKING)
    dp.register_message_handler(chat_gpt_answer, state = BotStates.CHAT_GPT)
    dp.register_message_handler(set_greet_text, state = BotStates.SET_GREED_TEXT)

from create_bot import get_channel
import asyncio
from aiogram import types
from aiogram.dispatcher import Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from utils import *
from states import BotStates
from db.account import Bots
from db.account import *
from greet import greeting_request_handler
import re
from datetime import datetime

request_type = "off"
options = {
    'Не вибрано': "off", 
    '✅ Автоприйом': "auto", 
    '❌ Автоприйом': "disable",
    "⌛ Відкласти прийом": "timeout_req",
    '🧾Прийняти певну кількість': 'amount',
}
channels = {}

kb = InlineKeyboardMarkup(inline_keyboard = [
    [InlineKeyboardButton(name, callback_data = data)] for name, data in list(options.items())[1:]
])

async def mode_selector(message: types.Message):
    channel = get_channel()
    if not channels.get(channel):
        channels[channel] = {"type": "off", "requests": [], "delay": None}
    type = next((key for key, value in options.items() if value == channels[channel]["type"]), None)
    await message.answer(f"Виберіть опцію:\nРежим: <b>{type}</b>", reply_markup = kb, parse_mode = "html")


async def option_handler(callback_query: types.CallbackQuery, state: FSMContext):
    bot = await Bots.get("id", callback_query.message.from_id)

    if bot:
        if callback_query.data == "chatgpt" and not bot["subscription"]:
            await callback_query.answer("Ця функці доступна лише після покупки тарифу", show_alert = True)
            return

    channel = get_channel()
    if not channels.get(channel):
        channels[channel] = {"type": "off", "requests": []}
    
    if channels[channel]["type"] == "off": 
        channels[channel]["type"] = callback_query.data
        button = get_button_by_callback_data(channels[channel]["type"], kb)
        button.text = "🔹" + button.text
        if callback_query.data == "amount":
            await callback_query.message.answer("Ввдедіть кількість:")
            await state.set_state(BotStates.AMOUNT)
        elif callback_query.data == "timeout_req":
            await callback_query.message.answer("Введіть час у форматі <b>00:00</b>", parse_mode = "html")
            await state.set_state(BotStates.TIMEOUT)
    else:
        button = get_button_by_callback_data(channels[channel]["type"], kb)
        button.text = button.text.removeprefix("🔹")
        
        channels[channel]["type"] = callback_query.data
        button = get_button_by_callback_data(channels[channel]["type"], kb)
        button.text = "🔹" + button.text
        if callback_query.data == "amount":
            await callback_query.message.answer("Ввдедіть кількість:")
            await state.set_state(BotStates.AMOUNT)
        elif callback_query.data == "timeout_req":
            await callback_query.message.answer("Введіть час у форматі <b>00:00</b>", parse_mode = "html")
            await state.set_state(BotStates.TIMEOUT)
    

    type = next((key for key, value in options.items() if value == channels[channel]["type"]), None)
    await callback_query.message.edit_text(f"Виберіть опцію:\nРежим: <b>{type}</b>", reply_markup = kb, parse_mode = "html")


async def auto_request(request: types.ChatJoinRequest):
    await asyncio.sleep(3)
    await request.approve()
   
async def disable_request(request: types.ChatJoinRequest):
    await asyncio.sleep(3)
    await request.decline()


async def set_amount(message: types.Message, state: FSMContext):
    try:
        channel = get_channel()
        requests = channels[channel]["requests"]
        to = int(message.text)
        
        counter = 0
        for request in requests[:to]:
            try:
                counter += 1
                await request.approve()
            except:
                continue

        await message.answer(f"Прийнято <b>{counter}</b> заявок", parse_mode = "html")
        await mode_selector(message)
        await state.finish()
    except:
        await message.answer("Невірне значення.Спробуйте ще раз:")

async def check_timeout(message: types.Message, delay: datetime, channel_id: str):
    channel = channels.get(channel_id)
    while delay > datetime.now() and channel["type"] == "timeout_req":
        await asyncio.sleep(10)
    
    channels[channel_id]["delay"] = None
    requests = channels[channel_id]["requests"]
    counter = 0
    for request in requests:
        try:
            counter += 1
            await request.approve()
        except:
            continue
    await message.answer(f"Прийнято <b>{counter}</b> заявок", parse_mode = "html")

async def set_timeout(message: types.Message, state: FSMContext):
    # try:
        channel = get_channel()
        current_datetime = datetime.today()
        date_time_regex = r'\d{2}:\d{2}'
        date_string = message.text

        if re.search(date_time_regex, date_string):
            time = datetime(current_datetime.year, current_datetime.month, current_datetime.day, hour=int(date_string[:2]), minute=int(date_string[3:5]))
            channels[channel]["delay"] = time
            await message.answer(f"Ви успішно відклали прийом заявок на <b>{time.strftime('%Y-%m-%d %H:%M:%S')}</b>", parse_mode = "html")
            await asyncio.create_task(check_timeout(message, time, channel))
            await state.finish()
        else:
            await message.answer("Невірне значення.Спробуйте ще раз:")
    # except:
    #     await message.answer("Невірне значення.Спробуйте ще раз:")


async def join_request_handler(request: types.ChatJoinRequest):
    await greeting_request_handler(request)
    channel_id = str(request.chat.id)
    channel = channels.get(channel_id)
    if channel:
        request_type = channel["type"]
        match request_type:
            case "off":
                channel["requests"].append(request)
            case "auto":
                await auto_request(request)
            case "disable":
                await disable_request(request)
            case "amount":
                channel["requests"].append(request)
            case "timeout_req":
                channel["requests"].append(request)

    
def register_request(dp: Dispatcher):
    dp.register_callback_query_handler(option_handler, lambda query: query.data in options.values())
    dp.register_chat_join_request_handler(join_request_handler)
    dp.register_message_handler(set_amount, state = BotStates.AMOUNT)
    dp.register_message_handler(set_timeout, state = BotStates.TIMEOUT)
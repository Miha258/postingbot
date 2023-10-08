from db.account import Channels
from db.account import Bots
from create_bot import bot, set_channel
from aiogram import types, Dispatcher
from states import *
from aiogram.dispatcher import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.callback_data import CallbackData
from posting import process_new_post
from aiogram.utils.exceptions import Unauthorized
from request import mode_selector
from utils import IsAdminFilter
from keyboards import *
from datetime import datetime
from greet import greet_menu
from content_plan import content_plan_list


channel_type = {
    "Постинг": "createpost",
    "Керування заявками": "request",
    "Привітання": "greet",
    "Контент-план": "content-plan"
}

async def choose_channels(message: types.Message, state: FSMContext):
    channels = await Channels.get("bot_id", bot.id, True)
    kb = InlineKeyboardMarkup(row_width = 1, inline_keyboard = [
        [InlineKeyboardButton("Додати канал +", callback_data = "add_channel")],
    ])
    if channels:
        kb.add(*[InlineKeyboardButton(channel["name"], callback_data = f"channel_{channel_type[message.text]}_{channel['chat_id']}") for channel in channels])
    
    kb.add(back_btn)
    await message.reply("Виберіть канал зі списку:", reply_markup = kb)
    await state.set_state(BotStates.CHOOSE_CHANNEL)


async def choose_channel_handler(callback_query: types.CallbackQuery, state: FSMContext):
    await state.finish()
    message = callback_query.message
    data = callback_query.data.split('_')
    operation_type = data[1]
    channel_id = data[2]
    await callback_query.message.delete() 
    _bot = await Bots.get("id", bot.id)

    if _bot:
        chat = await bot.get_chat(channel_id)
        subs_count = await chat.get_member_count()
        if subs_count > 1000 and _bot["subscription"] != 1:
            return await message.answer("Схоже у вас в каналі більше 1000 підписників.Офрміть <b>тариф</b> для використання бота", parse_mode = "html")
        
        if _bot["subscription"]:    
            if datetime.now() > datetime.strptime(_bot["subscription_to"], "%Y-%m-%d %H:%M:%S.%f"):
                await Bots.update("id", bot.id, subscription = False)
                return await message.answer("У вас закінчився тариф.Офрміть <b>тариф</b> для використання бота", parse_mode = "html")
    
    set_channel(channel_id)
    match operation_type:
        case "createpost":
            await process_new_post(message, state)
        case "request":
            await mode_selector(message)
        case "greet":
            await greet_menu(message)
        case "content-plan":
            await content_plan_list(message, state)

async def update_channel(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer("Перешліть мені повідомлення з каналу:")
    await state.set_state(BotStates.SET_CHANNEL)
   

async def update_channel_handler(message: types.Message, state: FSMContext):
    chat = message.forward_from_chat

    try:
        if not chat:
            await message.answer("Канал не знайдено.Спробуйте ще раз:")
        elif chat:
            await bot.get_chat(chat.id)
            channel = await Channels.get("chat_id", chat.id)
            if channel:
                if channel["bot_id"] == bot.id:
                    await message.answer("Цей канал вже додано.Спробуйте інший:")
                else:
                    await Channels(message.message_id, chat_id = chat.id, bot_id = bot.id, name = chat.full_name, subscribers = await chat.get_members_count())()
                    await message.answer("Канал успішно доданий!")
                    set_channel(str(chat.id))
                    await state.finish()
            else:
                await Channels(message.message_id, chat_id = chat.id, bot_id = bot.id, name = chat.full_name, subscribers = await chat.get_members_count())()
                await message.answer("Канал успішно доданий!")
                set_channel(str(chat.id))
                await state.finish()
    except Unauthorized:
        await message.answer("Схоже я не є учасником цього каналу.Спробуйте інший:")

def register_channels(dp: Dispatcher):
    dp.register_callback_query_handler(update_channel, CallbackData("add_channel").filter(), state = "*")
    dp.register_message_handler(choose_channels, lambda m: m.text in channel_type.keys(), IsAdminFilter(), state = "*")
    dp.register_message_handler(update_channel_handler, state = BotStates.SET_CHANNEL, content_types = types.ContentTypes.ANY)
    dp.register_callback_query_handler(choose_channel_handler, state = BotStates.CHOOSE_CHANNEL)
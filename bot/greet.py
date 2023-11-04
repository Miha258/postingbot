from aiogram import types
from aiogram.dispatcher import Dispatcher
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton, ReplyKeyboardMarkup
from aiogram.dispatcher import FSMContext
from states import BotStates, CustomGreetSatates
from utils import *
from create_bot import bot, get_channel , storage
import re
import asyncio
from db.account import Bots, Users, Greetings
from chatgpt import *
from utils import fetch_media_bytes

channels = {}
options = {
    '🔡Капча': "bot_checking", 
    "🤖ChatGPT": "chatgpt",
    "💌 Повідомлення": "set_greet_text"
}
channels = {}

def get_greet_options_kb():
    channel = get_channel()
    options_list = list(options.items())
    options_list.pop()
    kb = InlineKeyboardMarkup(inline_keyboard = [
        [InlineKeyboardButton(name + " Вкл.", callback_data = data)] 
        if data in channels[channel]["types"] 
        else [InlineKeyboardButton(name + " Викл.", callback_data = data)] 
        for name, data in options_list
    ])
    kb.add(InlineKeyboardButton("💌 Повідомлення", callback_data = "set_greet_text"))
    return kb

async def custom_greatings_kb():
    greetings = await Greetings.get('channel_id', get_channel(), True)
    kb = InlineKeyboardMarkup()
    if greetings:
        for greet in greetings:
            kb.inline_keyboard.append(
                [
                    InlineKeyboardButton(
                        f'⏳{greet["delay"]}m ❌{greet["autodelete"]}m',
                        callback_data = '*'
                    ),
                    InlineKeyboardButton(
                        greet['greet_text'],
                        callback_data = f'edit_custom_greet_{greet["id"]}'
                    )
                ]
            )
            

    kb.add(InlineKeyboardButton('Додати', callback_data = 'add_custom_greet'))
    kb.add(InlineKeyboardButton('Редагувати', callback_data = 'edit_button_greet_notify'))
    return kb


def timeout_selector_kb():
    timeouts = [
        '0.5m', '1m', '2m',
        '3m', '5m', '10m',
        '15m', '20m', '25m',
        '30m', '45m', '60m'
    ]

    kb = InlineKeyboardMarkup(inline_keyboard = [[InlineKeyboardButton(timeout, callback_data = f'set_greet_timeout_{timeout.removesuffix("m")}') for timeout in timeouts]])
    return kb 


async def edit_custom_greating_kb(greet_id: int):
    greeting: dict = await Greetings.get('id', greet_id)
    buttons: str = greeting['buttons']
    autodelete: int = greeting['autodelete']
    delay: int = greeting['delay']

    kb = InlineKeyboardMarkup(inline_keyboard = [
        [InlineKeyboardButton(f'Автовидалення: {autodelete}m' if autodelete else 'Автовидалення', callback_data = f'custom_greet_autodelete_{greet_id}')],
        [InlineKeyboardButton(f'Затримка: {delay}m' if delay else f'Затримка', callback_data = f'custom_greet_delay_{greet_id}')],
        [InlineKeyboardButton('Видалити кнопки', callback_data = f'remove_custom_greet_buttons_{greet_id}') if 
        buttons else InlineKeyboardButton("Додати кнопки", callback_data = f'add_custom_greet_buttons_{greet_id}') ],
        [InlineKeyboardButton('Видалити', callback_data = f'delete_greet_{greet_id}')],
        [InlineKeyboardButton('Назад', callback_data = f'stop_editing_greet_{greet_id}')]
    ])
    if buttons:
        buttons_list = buttons.split('\n')
        for button in buttons_list:
            try:
                name, url = button.split('-', 1)
                kb.inline_keyboard.insert(0, [InlineKeyboardButton(name, url)])
            except ValueError:
                pass
    return kb


async def greet_menu(message: types.Message):
    channel = get_channel()
    if not channels.get(channel):
        channels[channel] = {
            "types": []
        }
    await message.answer('Виберіть опцію:', reply_markup = get_greet_options_kb(), parse_mode = 'html')


async def option_handler(callback_query: types.CallbackQuery, state: FSMContext):
    bot = await Bots.get("id", callback_query.message.from_id)
    type = callback_query.data
    if bot:
        if type == "chatgpt" and not bot["subscription"]:
            return await callback_query.answer("Ця функці доступна лише після покупки тарифу", show_alert = True)
    
    channel = get_channel()
    if type in channels[channel]['types']:
         channels[channel]['types'].remove(type)
    else:
        channels[channel]['types'].append(type)

    if type == "set_greet_text":
        await callback_query.message.answer(
    """
    💌 Повідомлення

    Налаштовуй повідомлення, які отримає користувач при взаємодії з підключеним каналом.
    """, reply_markup = await custom_greatings_kb())
    else:
        await callback_query.message.edit_reply_markup(get_greet_options_kb())


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


async def send_custom_greet_to_user(request: types.ChatJoinRequest):
    channel = request.chat.id
    greets = await Greetings.get('channel_id', channel, True)
    if greets:
        for greet in greets:
            autodelete: int = greet['autodelete']
            delay: int = greet['delay']
            greet_text: int = greet['greet_text']
            buttons: str = greet['buttons']
            image: bytes = greet['image']
            await asyncio.sleep(delay * 60)
            
            kb = InlineKeyboardMarkup()
            if buttons:
                for button in buttons.split('\n'):
                    if button:
                        name, url =  button.split('-')
                        kb.add(InlineKeyboardButton(name, url))
            
            if image:
                msg = await bot.send_photo(request.from_user.id, image, greet_text, reply_markup = kb, parse_mode = 'html') 
            else:
                msg = await bot.send_message(request.from_user.id, greet_text, reply_markup = kb, parse_mode = 'html')
            
            if autodelete:  
                await asyncio.sleep(autodelete * 60)
                await msg.delete()


async def greeting_request_handler(request: types.ChatJoinRequest):
    asyncio.create_task(send_custom_greet_to_user(request))
    channel: str = channels.get(str(request.chat.id))
    if channel:
        request_types = channel['types']
        for type in request_types:
            match type:
                case "bot_checking":
                    await bot_checking(request)
                case "chatgpt":
                    await chat_gpt(request)
                        

async def add_custom_greet(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.message.answer("Надішліть текст та фото/відео:")
    await state.set_state(CustomGreetSatates.MEDIA)


async def custom_greet_buttons(message: types.Message, state: FSMContext):
    await state.update_data({'greet_text': message.caption or message.html_text, 'media': message.photo[-1] if message.photo else message.video})
    await message.answer("Введіть кнопку у форматі: \n<em>1. Кнопка - посилання</em>\n<em>2. Кнопка - посилання</em>\n<em>3. Кнопка - посилання</em>",parse_mode = "html")
    await state.set_state(CustomGreetSatates.BUTTONS)


async def procces_custom_greet(message: types.Message, state: FSMContext):
    regex_pattern = r'([^\-]+) - ([^\n]+)'

    matches = re.findall(regex_pattern, message.text)
    buttons = ""
    if matches:
        for name, link in matches:
            try:
                InlineKeyboardButton(name, link)
            except:
                pass
            else:
                buttons += (name + '-' + link + '\n')
    
    async with state.proxy() as data:
        greet_text = data['greet_text']
        media: types.PhotoSize | types.Video = data['media']
        media_data = None
        if media:
            file = await media.get_url()
            media_data = await fetch_media_bytes(file)
    
    await Greetings(message.message_id, bot_id = bot.id, greet_text = greet_text, channel_id = get_channel(), autodelete = 0, delay = 0, buttons = buttons, image = media_data)()
    await message.answer(
    """
    💌 Повідомлення

    Налаштовуй повідомлення, які отримає користувач при взаємодії з підключеним каналом.
    """, reply_markup = await custom_greatings_kb())
    await state.finish()


async def edit_button_greet_notify(callback_query: types.CallbackQuery):
    await callback_query.answer('Оберіть привітання, яке хочете відредагувати у правій колонці', show_alert = True)


async def edit_custom_greet(callback_query: types.CallbackQuery, state: FSMContext):
    data = callback_query.data
    greet_id = int(data.split('_')[-1])
    greet = await Greetings.get('id', greet_id)
    
    await callback_query.message.answer(greet['greet_text'], reply_markup = await edit_custom_greating_kb(greet_id))
    await state.set_state(CustomGreetSatates.GREET_EDITING)


async def edit_custom_greet_handler(callback_query: types.CallbackQuery, state: FSMContext):
    data = callback_query.data
    greet_id = int(data.split('_')[-1])
    await state.set_data({'greet_id': greet_id})

    data = data.split('_')[:-1]
    action = "_".join(data)
    
    match action:
        case "custom_greet_autodelete":
            await state.set_state(CustomGreetSatates.EDIT_AUTODELETE)
            await callback_query.message.edit_text("Оберіть, через скільки ваше привітання буде видалено:", reply_markup = timeout_selector_kb())
        case "custom_greet_delay":
            await state.set_state(CustomGreetSatates.EDIT_DELAY)
            await callback_query.message.edit_text("Оберіть затримку надсилання привітання:", reply_markup = timeout_selector_kb())
        case "remove_custom_greet_buttons":
            await remove_greet_buttons(callback_query, state)
        case "add_custom_greet_buttons":
            await callback_query.message.delete()
            await callback_query.message.answer("Введіть кнопку у форматі: \n<em>1. Кнопка - посилання</em>\n<em>2. Кнопка - посилання</em>\n<em>3. Кнопка - посилання</em>", parse_mode = "html")
            await state.set_state(CustomGreetSatates.EDIT_BUTTONS)
        case 'delete_greet':
            await delete_greet(callback_query, state)
        case 'stop_editing_greet':
            await callback_query.message.answer(
            """
            💌 Повідомлення

            Налаштовуй повідомлення, які отримає користувач при взаємодії з підключеним каналом.
            """, reply_markup = await custom_greatings_kb())
            await state.finish()

async def edit_greet_autodelete(callback_query: types.CallbackQuery, state: FSMContext):
    autodelete = float(callback_query.data.split('_')[-1])
    greet_id = (await state.get_data())['greet_id']
    greet = await Greetings.update('id', greet_id, autodelete = autodelete)
    
    await callback_query.message.edit_text(greet['greet_text'], reply_markup = await edit_custom_greating_kb(greet_id))
    await state.set_state(CustomGreetSatates.GREET_EDITING)

async def edit_greet_delay(callback_query: types.CallbackQuery, state: FSMContext):
    delay = float(callback_query.data.split('_')[-1])
    greet_id = (await state.get_data())['greet_id']
    greet = await Greetings.update('id', greet_id, delay = delay)
    
    await callback_query.message.edit_text(greet['greet_text'], reply_markup = await edit_custom_greating_kb(greet_id))
    await state.set_state(CustomGreetSatates.GREET_EDITING)

async def edit_greet_buttons(message: types.Message, state: FSMContext):
    matches = message.text.split('\n')
    buttons = ""
    try:
        if matches:
            for btn in matches:
                name, link = btn.split(' - ')
                InlineKeyboardButton(name, link)
                await message.edit_text(message.html_text)
                buttons += (name + '-' + link + '\n')
    
        greet_id = (await state.get_data())['greet_id']
        greet = await Greetings.update('id', greet_id, buttons = buttons)

        await message.answer(greet['greet_text'], reply_markup = await edit_custom_greating_kb(greet_id))
        await state.set_state(CustomGreetSatates.GREET_EDITING)
    except ValueError:
        await message.answer("Некоректний формат.Cпробуйте ще раз")

async def remove_greet_buttons(callback_query: types.CallbackQuery, state: FSMContext):
    greet_id = (await state.get_data())['greet_id']
    await Greetings.update('id', greet_id, buttons = None)
    
    await callback_query.message.edit_reply_markup(await edit_custom_greating_kb(greet_id))
    await state.set_state(CustomGreetSatates.GREET_EDITING)


async def edit_greet_text(message: types.Message, state: FSMContext):
    greet_id = (await state.get_data())['greet_id']
    await Greetings.update('id', greet_id, greet_text = message.html_text)

    await message.edit_text(message.html_text)
    await state.set_state(CustomGreetSatates.GREET_EDITING)


async def delete_greet(callback_query: types.CallbackQuery, state: FSMContext):
    greet_id = (await state.get_data())['greet_id']
    await Greetings.delete(id = greet_id)
    
    await callback_query.message.delete()
    await callback_query.message.answer(
    """
    💌 Повідомлення

    Налаштовуй повідомлення, які отримає користувач при взаємодії з підключеним каналом.
    """, reply_markup = await custom_greatings_kb())
    await state.finish()


def register_greet(dp: Dispatcher):
    dp.register_callback_query_handler(add_custom_greet, lambda cb: cb.data == 'add_custom_greet')
    dp.register_message_handler(custom_greet_buttons, state = CustomGreetSatates.MEDIA, content_types = types.ContentTypes.TEXT | types.ContentTypes.PHOTO | types.ContentTypes.VIDEO)
    dp.register_message_handler(procces_custom_greet, state = CustomGreetSatates.BUTTONS)
    dp.register_callback_query_handler(edit_custom_greet, lambda cb: "edit_custom_greet" in cb.data)
    dp.register_callback_query_handler(edit_custom_greet_handler, state = CustomGreetSatates.GREET_EDITING)
    dp.register_message_handler(edit_greet_buttons, state = CustomGreetSatates.EDIT_BUTTONS)
    dp.register_callback_query_handler(edit_button_greet_notify, lambda cb: cb.data == 'edit_button_greet_notify')
    dp.register_callback_query_handler(edit_greet_autodelete, state = CustomGreetSatates.EDIT_AUTODELETE)
    dp.register_callback_query_handler(edit_greet_delay, state = CustomGreetSatates.EDIT_DELAY)
    dp.register_callback_query_handler(option_handler, lambda cb: cb.data in options.values())
    dp.register_message_handler(check_season, state = BotStates.BOT_CHECKING)
    dp.register_message_handler(chat_gpt_answer, state = BotStates.CHAT_GPT)
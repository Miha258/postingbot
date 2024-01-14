from aiogram import types
from aiogram.dispatcher import Dispatcher
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton, ReplyKeyboardMarkup
from aiogram.dispatcher import FSMContext
from states import BotStates, CustomGreetSatates
from utils import *
from create_bot import bot, get_channel, storage
import re
import asyncio
from db.account import Bots, Users, Greetings, Channels
from chatgpt import *
from keyboards import edit_capcha_kb

channels = {}
options = {
    '🔡Капча': "bot_checking", 
    "🤖ChatGPT": "chatgpt",
    "💌 Повідомлення": "set_greet_text"
}
back_to_custom_greet_menu_kb = lambda greet_id: InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton('Повернутися', callback_data = f"back_to_edit_greet_menu_{greet_id}")]])
back_to_custom_capcha_menu_kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton('Повернутися', callback_data = f"back_to_custom_capcha_menu")]])

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


def timeout_selector_kb(greet_id):
    timeouts = [
        '0.5m', '1m', '2m',
        '3m', '5m', '10m',
        '15m', '20m', '25m',
        '30m', '45m', '60m'
    ]

    kb = InlineKeyboardMarkup(inline_keyboard = [[InlineKeyboardButton(timeout, callback_data = f'set_greet_timeout_{timeout.removesuffix("m")}') for timeout in timeouts]])
    kb.add(InlineKeyboardButton('Повернутися', callback_data = f"back_to_edit_greet_menu_{greet_id}"))
    return kb 


async def edit_custom_greating_kb(greet_id: int):
    greeting: dict = await Greetings.get('id', greet_id)
    buttons: str = greeting['buttons']
    autodelete: int = greeting['autodelete']
    delay: int = greeting['delay']

    kb = InlineKeyboardMarkup(inline_keyboard = [
        [InlineKeyboardButton('Змінити текст', callback_data = f'custom_greet_edit_text_{greet_id}')],
        [InlineKeyboardButton(f'Автовидалення: {autodelete}m' if autodelete else 'Автовидалення', callback_data = f'custom_greet_autodelete_{greet_id}')],
        [InlineKeyboardButton('Редагувати медіа', callback_data = f'edit_custom_greet_media_{greet_id}')],
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


async def greet_menu(message: types.Message, state: FSMContext):
    await state.finish()
    channel = get_channel()
    if not channels.get(channel):
        channels[channel] = {
            "types": []
        }
    await message.answer('Виберіть опцію:', reply_markup = get_greet_options_kb(), parse_mode = 'html')


async def option_handler(callback_query: types.CallbackQuery):
    bot = await Bots.get("id", callback_query.message.from_id)
    type = callback_query.data
    if bot:
        if type == "chatgpt" and not bot["subscription"]:
            return await callback_query.answer("Ця функці доступна лише після покупки тарифу", show_alert = True)
    
    channel = get_channel()
    if type == 'bot_checking':
        _channel = await Channels.get("chat_id", channel)
        capcha = _channel['capcha']
        if capcha is None:
            capcha = (await Channels.update("id", _channel['id'], capcha = "Пройдіть перевірку на бота - Відмовитися | Ви відмовилися від перевірки , Підтвердити | Перевірку пройдено"))['capcha']
        capcha_text, capcha_btns = capcha.split(' - ')
        return await callback_query.message.edit_text(f'<b>Текст капчі:</b> \n\n{capcha_text if capcha_text else "Немає"}', reply_markup = edit_capcha_kb(type in channels[channel]['types'], capcha_btns))

    else:
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


async def change_bot_checking_status(callback_query: types.CallbackQuery, state: FSMContext):
    channel = get_channel()
    type = "bot_checking"
    if type in channels[channel]['types']:
        channels[channel]['types'].remove(type)
    else:
        channels[channel]['types'].append(type)
    capcha = (await Channels.get("chat_id", channel))['capcha']
    capcha_btns = capcha.split(' - ')[1]
    if callback_query.data == "set_capcha_status":
        await callback_query.message.edit_reply_markup(edit_capcha_kb(type in channels[channel]['types'], capcha_btns))
    elif callback_query.data == "back_to_custom_capcha_menu":
        _channel = await Channels.get("chat_id", channel)
        capcha = _channel['capcha']
        capcha_text, capcha_btns = capcha.split(' - ')
        await callback_query.message.edit_text(f'<b>Текст капчі:</b> \n\n{capcha_text if capcha_text else "Немає"}', reply_markup = edit_capcha_kb(type in channels[channel]['types'], capcha_btns))
        await state.finish()

async def edit_capcha(callback_query: types.CallbackQuery, state: FSMContext): 
    await callback_query.message.answer('Введіть текст у форматі \n\n <strong>Текст капчі - кнопка1 | відповідь1 , кнопка2 | відповідть2</strong>', reply_markup = back_to_custom_capcha_menu_kb)
    await state.set_state(BotStates.EDITING_CAPCHA)


async def update_bot_checking_text(message: types.Message, state: FSMContext):
    try:
        capcha_text, capcha_btns = message.text.split(' - ')
        if ' , ' not in message.text:
            reply, answer = capcha_btns.split(' | ')
        else:
            capcha_data = capcha_btns.split(' , ')
            capcha_answers = {}
            for data in capcha_data:
                reply, answer = data.split(' | ')
    except:
        await message.answer('Невірний формат капчі.Cпробуйте ще раз:')
    else:
        capcha_answers[reply] = answer
        channel = get_channel()
        channel_id = (await Channels.get("chat_id", channel))['id']
        capcha = (await Channels.update("id", channel_id, capcha = message.text))['capcha']
        capcha_text, capcha_btns = capcha.split(' - ')
        await message.answer(f'<b>Текст капчі:</b> \n\n{capcha_text if capcha_text else "Немає"}', reply_markup = edit_capcha_kb(type in channels[channel]['types'], capcha_btns))
        await state.finish()
    

async def back_to_greet_menu(callback_query: types.CallbackQuery, state: FSMContext):
    channel = get_channel()
    if not channels.get(channel):
        channels[channel] = {
            "types": []
        }
    await callback_query.message.edit_text('Виберіть опцію:', reply_markup = get_greet_options_kb(), parse_mode = 'html')
    await state.finish()

async def bot_checking(request: types.ChatJoinRequest):
    capcha = (await Channels.get("chat_id", request.chat.id))['capcha']
    capcha_text, capcha_btns = capcha.split(' - ')
    btns = []
    if capcha_btns:
        capcha_data = capcha_btns.split(' , ')
        for data in capcha_data:
            reply = data.split(' | ')[0]
            btns.append(KeyboardButton(reply))
        
    await bot.send_message(request.user_chat_id, capcha_text, reply_markup = ReplyKeyboardMarkup(keyboard = [btns], resize_keyboard = True))
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


async def check_capcha(message: types.Message, state: FSMContext):
    if not await Users.get('id', message.from_id):
        await Users(message.from_id, bot_id = bot.id)()
    
    channel = get_channel()
    capcha = (await Channels.get("chat_id", channel))['capcha']
    capcha_btns = capcha.split(' - ')[1]
    capcha_answers = {}
    if ' , ' not in capcha_btns:
        reply, answer = capcha_btns.split(' | ')
        capcha_answers[reply] = answer
    else:
        capcha_data = capcha_btns.split(' , ')
        for data in capcha_data:
            reply, answer = data.split(' | ')
            capcha_answers[reply] = answer
    
    reply = capcha_answers.get(message.text)
    if reply:
        await message.answer(reply)
        await send_custom_greet_to_user(message.from_id)
        await state.finish()


async def send_custom_greet_to_user(user_id: int):
    greets = await Greetings.get('bot_id', bot.id, True)
    if greets:
        for greet in greets:
            autodelete: int = greet['autodelete']
            delay: int = greet['delay']
            greet_text: int = greet['greet_text']
            buttons: str = greet['buttons']
            media: bytes = greet['image']
            await asyncio.sleep(delay * 60)
            
            kb = InlineKeyboardMarkup()
            if buttons:
                for button in buttons.split('\n'):
                    if button:
                        print(button)
                        name, url =  button.split(' - ')
                        kb.add(InlineKeyboardButton(name, url))
            if media:
                file = await fetch_media_bytes(media)
                is_video = types.InputMediaVideo(file).duration
                if is_video:
                    msg = await bot.send_video(user_id, file, greet_text, reply_markup = kb, parse_mode = 'html') 
                elif not is_video:
                    msg = await bot.send_photo(user_id, file, greet_text, reply_markup = kb, parse_mode = 'html') 
            else:
                msg = await bot.send_message(user_id, greet_text, reply_markup = kb, parse_mode = 'html')
            
            if autodelete:  
                await asyncio.sleep(autodelete * 60)
                await msg.delete()


async def greeting_request_handler(request: types.ChatJoinRequest):
    channel: str = channels.get(str(request.chat.id))

    if channel:
        request_types = channel['types']
        if 'set_greet_text' in request_types and len(request_types) == 1:
            await send_custom_greet_to_user(request.from_user.id)
        else:
            if request_types:
                for type in request_types:
                    match type:
                        case "bot_checking":
                            await bot_checking(request)
                        case "chatgpt":
                            await chat_gpt(request)
    else:
        await send_custom_greet_to_user(request.from_user.id)
                        

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
            media_data = await media.get_url()
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
    greet = (await Greetings.get('id', greet_id)).data
    media = greet.get('image')
    text = greet.get('greet_text')
    if media:
        file = await fetch_media_bytes(media)
        is_video = types.InputMediaVideo(file).duration
        if is_video:
            await callback_query.message.answer_video(file, text, reply_markup = await edit_custom_greating_kb(greet_id), parse_mode = 'html') 
        elif not is_video:
            await callback_query.message.answer_photo(file, text, reply_markup = await edit_custom_greating_kb(greet_id), parse_mode = 'html') 
    else:
        await callback_query.message.answer(text, reply_markup = await edit_custom_greating_kb(greet_id))
    await state.set_state(CustomGreetSatates.GREET_EDITING)

async def edit_custom_greet_handler(callback_query: types.CallbackQuery, state: FSMContext):
    data = callback_query.data
    greet_id = int(data.split('_')[-1])
    message = callback_query.message
    media = message.photo[-1] if message.photo else message.video
    await state.set_data({'greet_id': greet_id})

    data = data.split('_')[:-1]
    action = "_".join(data)
    
    match action:   
        case "custom_greet_edit_text":
            await state.set_state(CustomGreetSatates.EDIT_TEXT)
            if media:
                await message.edit_caption("Введіть новий текст привітання:", reply_markup = back_to_custom_greet_menu_kb(greet_id))
            else:
                await message.edit_text("Введіть новий текст привітання:", reply_markup = back_to_custom_greet_menu_kb(greet_id))
        case "custom_greet_autodelete":
            await state.set_state(CustomGreetSatates.EDIT_AUTODELETE)
            if media:
                await message.edit_caption("Оберіть, через скільки ваше привітання буде видалено:", reply_markup = timeout_selector_kb(greet_id))
            else:
                await message.edit_text("Оберіть, через скільки ваше привітання буде видалено:", reply_markup = timeout_selector_kb(greet_id))
        case "custom_greet_delay":
            await state.set_state(CustomGreetSatates.EDIT_DELAY)
            if media:
                await message.edit_caption("Оберіть затримку надсилання привітання:", reply_markup = timeout_selector_kb(greet_id))
            else:
                await message.edit_text("Оберіть затримку надсилання привітання:", reply_markup = timeout_selector_kb(greet_id))
        case "remove_custom_greet_buttons":
            await remove_greet_buttons(callback_query, state)
        case "add_custom_greet_buttons":
            await message.delete()
            await message.answer("Введіть кнопку у форматі: \n<em>1. Кнопка - посилання</em>\n<em>2. Кнопка - посилання</em>\n<em>3. Кнопка - посилання</em>", reply_markup = back_to_custom_greet_menu_kb(greet_id), parse_mode = "html")
            await state.set_state(CustomGreetSatates.EDIT_BUTTONS)
        case 'delete_greet':
            await delete_greet(callback_query, state)
        case "edit_custom_greet_media":
            await message.answer("Введіть фото/відео:", reply_markup = back_to_custom_greet_menu_kb(greet_id))
            await state.set_state(CustomGreetSatates.EDIT_MEDIA)
        case 'stop_editing_greet':
            await message.answer(
            """
💌 Повідомлення

Налаштовуй повідомлення, які отримає користувач при взаємодії з підключеним каналом.
            """, reply_markup = await custom_greatings_kb())
            await state.finish()

async def back_to_edit_greet_menu(callback_query: types.CallbackQuery, state: FSMContext):
    data = callback_query.data
    greet_id = int(data.split('_')[-1])
    greet = (await Greetings.get('id', greet_id)).data
    media = greet.get('image')
    text = greet.get('greet_text')
    if media:
        await callback_query.message.edit_caption(text, reply_markup = await edit_custom_greating_kb(greet_id)) 
    else:
        await callback_query.message.answer(text, reply_markup = await edit_custom_greating_kb(greet_id))
    await state.set_state(CustomGreetSatates.GREET_EDITING)

async def edit_greet_autodelete(callback_query: types.CallbackQuery, state: FSMContext):
    autodelete = float(callback_query.data.split('_')[-1])
    greet_id = (await state.get_data())['greet_id']
    greet = await Greetings.update('id', greet_id, autodelete = autodelete)
    message = callback_query.message
    media = message.photo[-1] if message.photo else message.video

    if media:
        await message.edit_caption(greet['greet_text'], reply_markup = await edit_custom_greating_kb(greet_id))
    else:
        await message.edit_text(greet['greet_text'], reply_markup = await edit_custom_greating_kb(greet_id))
    await state.set_state(CustomGreetSatates.GREET_EDITING)

async def edit_greet_delay(callback_query: types.CallbackQuery, state: FSMContext):
    delay = float(callback_query.data.split('_')[-1])
    greet_id = (await state.get_data())['greet_id']
    greet = await Greetings.update('id', greet_id, delay = delay)
    message = callback_query.message
    media = message.photo[-1] if message.photo else message.video

    if media:
        await message.edit_caption(greet['greet_text'], reply_markup = await edit_custom_greating_kb(greet_id))
    else:
        await message.edit_text(greet['greet_text'], reply_markup = await edit_custom_greating_kb(greet_id))
    await state.set_state(CustomGreetSatates.GREET_EDITING)

async def edit_greet_buttons(message: types.Message, state: FSMContext):
    matches = message.text.split('\n')
    buttons = ""
    try:
        if matches:
            for btn in matches:
                name, link = btn.split(' - ')
                InlineKeyboardButton(name, link)
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
    greet = await Greetings.update('id', greet_id, greet_text = message.html_text)
    media = greet.data.get('image')

    if media:
        file = await fetch_media_bytes(media)
        is_video = types.InputMediaVideo(file).duration
        if is_video:
            await message.answer_video(file, message.html_text, reply_markup = await edit_custom_greating_kb(greet_id))
        elif not is_video:
            await message.answer_photo(file, message.html_text, reply_markup = await edit_custom_greating_kb(greet_id))     
    else:
        await message.answer(message.html_text, reply_markup = await edit_custom_greating_kb(greet_id))

    await state.set_state(CustomGreetSatates.GREET_EDITING)


async def edit_greet_media(message: types.Message, state: FSMContext):
    greet_id = (await state.get_data())['greet_id']
    media = message.photo[-1] if message.photo else message.video
    greet = await Greetings.update('id', greet_id, image = await media.get_url())

    if isinstance(media, types.PhotoSize):
        await message.answer_photo(media.file_id, greet['greet_text'], reply_markup = await edit_custom_greating_kb(greet_id))
    elif isinstance(media, types.Video):
        await message.answer_video(media.file_id, caption = greet['greet_text'], reply_markup = await edit_custom_greating_kb(greet_id))
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
    dp.register_message_handler(greet_menu, lambda m: m.text == 'Привітання', IsAdminFilter(), IsChannel(), state = "*")
    dp.register_callback_query_handler(back_to_greet_menu, lambda cb: cb.data == 'back_to_greet_menu')
    dp.register_callback_query_handler(back_to_edit_greet_menu, lambda cb: 'back_to_edit_greet_menu' in cb.data, state = "*")
    dp.register_callback_query_handler(add_custom_greet, lambda cb: cb.data == 'add_custom_greet')
    dp.register_callback_query_handler(edit_capcha, lambda cb: cb.data in 'edit_capcha')
    dp.register_callback_query_handler(change_bot_checking_status, lambda cb: cb.data in ('set_capcha_status', 'back_to_custom_capcha_menu'), state = "*")
    dp.register_message_handler(update_bot_checking_text, state = BotStates.EDITING_CAPCHA)
    dp.register_message_handler(custom_greet_buttons, state = CustomGreetSatates.MEDIA, content_types = types.ContentTypes.TEXT | types.ContentTypes.PHOTO | types.ContentTypes.VIDEO)
    dp.register_message_handler(procces_custom_greet, state = CustomGreetSatates.BUTTONS)
    dp.register_callback_query_handler(edit_custom_greet, lambda cb: "edit_custom_greet" in cb.data)
    dp.register_callback_query_handler(edit_custom_greet_handler, state = CustomGreetSatates.GREET_EDITING)
    dp.register_message_handler(edit_greet_text, state = CustomGreetSatates.EDIT_TEXT)
    dp.register_message_handler(edit_greet_buttons, state = CustomGreetSatates.EDIT_BUTTONS)
    dp.register_message_handler(edit_greet_media, state = CustomGreetSatates.EDIT_MEDIA, content_types = types.ContentTypes.PHOTO | types.ContentTypes.VIDEO) 
    dp.register_callback_query_handler(edit_button_greet_notify, lambda cb: cb.data == 'edit_button_greet_notify')
    dp.register_callback_query_handler(edit_greet_autodelete, state = CustomGreetSatates.EDIT_AUTODELETE)
    dp.register_callback_query_handler(edit_greet_delay, state = CustomGreetSatates.EDIT_DELAY)
    dp.register_callback_query_handler(option_handler, lambda cb: cb.data in options.values())
    dp.register_message_handler(check_capcha, state = BotStates.BOT_CHECKING)
    dp.register_message_handler(chat_gpt_answer, state = BotStates.CHAT_GPT)
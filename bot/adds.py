from aiogram import types, Dispatcher
from states import BotAdds
from aiogram.dispatcher import FSMContext
from db.account import Users, Adds, Bots
from keyboards import *
from create_bot import bot
import re
import asyncio
from utils import *
from aiogram.utils.exceptions import BadRequest

data = {}

def get_edit_adds_kb():
    kb = InlineKeyboardMarkup(inline_keyboard = [
    [
        InlineKeyboardButton("Змінити текст", callback_data = f"edit_adds_text"),
        InlineKeyboardButton("Прикріпити медіа", callback_data = "edit_adds_media")
    ],
    [
        InlineKeyboardButton("Додати кнопки", callback_data = f"edit_adds_buttons"),
    ],  
    [
        InlineKeyboardButton("Відкласти", callback_data = f"delay_adds"),
        InlineKeyboardButton("Опублікувати", callback_data = f"create_adds")
    ]
    ])

    url_buttons = data.get("buttons")
    if url_buttons:
        row_btns = []
        column_buttons = 0
        for btn in url_buttons:
            if isinstance(btn, list):
                kb.inline_keyboard.insert(column_buttons, btn)
                column_buttons += 1
            elif isinstance(btn, InlineKeyboardButton):
                row_btns.append(btn)
        if row_btns:
            kb.inline_keyboard.insert(0, row_btns)
        kb.inline_keyboard.insert(len(url_buttons), [
            InlineKeyboardButton("Прибрати URL-кнопки", callback_data = "remove_url_buttons")
        ])
    kb.add(back_btn)
    return kb

async def process_new_add(callback_query: types.CallbackQuery, state: FSMContext):
    await state.finish()
    data.clear()
    data["adds_text"] = None
    data["buttons"] = []
    data["media"] = None
    data["delay"] = None
    data["datetime"] = (await state.get_data()).get('datetime')
    await callback_query.message.answer("Надішліть текст, картику або відео оголошення:")
    await state.set_state(BotAdds.TEXT)


async def adds_handler(callback_query: types.CallbackQuery, state: FSMContext):
    message = callback_query.message
    match callback_query.data:
        case "edit_adds_text":
            await message.answer("Надішліть текст, фото/відео:", reply_markup = back_to_menu())
            await state.set_state(BotAdds.TEXT)
        case "edit_adds_media":
            await message.answer("Надішліть нове фото/відео оголошення:", reply_markup = back_to_menu())
            await state.set_state(BotAdds.MEDIA)
        case "edit_adds_buttons":
            await state.set_state(BotAdds.BTN)
            await message.reply("Введіть кнопку у форматі: \n<em>1. Кнопка - посилання</em>\n<em>2. Кнопка - посилання</em>\n<em>3. Кнопка - посилання</em>", reply_markup = skip_menu(), parse_mode = "html")
        case "delay_adds":
            await state.set_state(BotAdds.DATE)
            await message.reply("Виберіть дату", reply_markup = get_calendar(), parse_mode = "html")
        case "create_adds":
            await save_add(message, state, get_user_kb(data))

async def edit_adds_text(message: types.Message, state: FSMContext):
    if not data["adds_text"] and not data["media"]:
        data["media"] = message.photo[-1] if message.photo else message.video
    if not data["buttons"] and message.reply_markup:
        data["buttons"] = message.reply_markup.inline_keyboard
    
    if message.text or message.caption:
        data["adds_text"] = message.md_text or message.caption if data.get("parse_mode") == types.ParseMode.MARKDOWN else message.html_text or message.caption
    else:
        data["media"] = message.photo[-1] if message.photo else message.video
        return await message.answer('Тепер введіть текст оголошення:')
    
    media = data.get('media')
    kb = get_edit_adds_kb()
    if media:
        if isinstance(media, types.PhotoSize):
            await message.answer_photo(media.file_id, message.html_text, reply_markup = kb)  
        elif isinstance(media, types.Video):
            await message.answer_video(media.file_id, message.html_text, reply_markup = kb)
    else:
        await message.answer(message.html_text, reply_markup = kb)
    await state.set_state(BotAdds.EDITING)


async def edit_adds_media(message: types.Message, state: FSMContext):
    data["media"] = message.photo[-1] if message.photo else message.video
    kb = get_edit_adds_kb()
    media = data.get('media')
    if media:
        if isinstance(media, types.PhotoSize):
            await message.answer_photo(media.file_id, caption = data["adds_text"], reply_markup = kb)
        elif isinstance(media, types.Video):
            await message.answer_video(media.file_id, caption = data["adds_text"], parse_mode = data.get("parse_mode"), reply_markup = kb)
    else:    
        await message.answer(data["adds_text"], reply_markup = kb)
    await state.set_state(BotAdds.EDITING)


async def edit_adds_buttons(message: types.Message, state: FSMContext):
    try:
        matches = message.text.split('\n')
        if matches:
            kb = types.InlineKeyboardMarkup(row_width = 1)
            for btn in matches:
                if '/' in btn:
                    rows = btn.split(' / ')
                    data["buttons"].append([InlineKeyboardButton(row.split(' - ')[0], row.split(' - ')[1]) for row in rows])
                else:
                    column_buttons = btn.split(' - ')
                    if len(column_buttons) > 1:
                        name, url = column_buttons
                        data["buttons"].append([InlineKeyboardButton(name, url)])
        kb = get_edit_adds_kb()
        media = data.get('media')
        if media:
            if isinstance(media, types.PhotoSize):
                await message.answer_photo(media.file_id, caption = data["text"], parse_mode = data.get("parse_mode"), reply_markup = kb)
            elif isinstance(media, types.Video):
                await message.answer_video(media.file_id, caption = data["text"], parse_mode = data.get("parse_mode"), reply_markup = kb)
        else:
            await message.answer(data["text"], parse_mode = data.get("parse_mode"), reply_markup = kb)
        await state.set_state(BotAdds.EDITING)
    except BadRequest:
        await message.answer("Некоректне посилання.Cпробуйте ще раз")
    except IndexError:
        await message.answer("Некоректний формат.Cпробуйте ще раз")
    except ValueError:
        await message.answer("Некоректний формат.Cпробуйте ще раз")
    

async def choose_date_handler(callback_query: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        date = callback_query.data.split(":")[1]
        data['date'] = datetime.datetime.strptime(date, "%Y-%m-%d").date()
        await callback_query.answer(f"Ви обрали {date}")

        
async def delay_adds_handler(message: types.Message, state: FSMContext):
    data = await state.get_data()
    date_time = data.get("datetime")
    if not date_time:
        date_time_regex = r'\d{2}:\d{2}'
        date_string = message.text
        date = data.get("date")
        
        if not date:
            return await message.answer("Ви не вибрали дату")
        try:
            if re.search(date_time_regex, date_string):
                time = datetime.datetime.strptime(date_string, "%H:%M").time()
                date = datetime.datetime.combine(date, time)
                if date <= datetime.datetime.now():
                    return await message.answer(f"Недійсна дата.Спробуйте ще раз")  
                
                data["delay"] = date
                kb = get_user_kb(data)
                await save_add(message, state, kb)
                await state.set_state(BotAdds.CHECK)
            else:                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            
                await message.answer("Невірний формат дати.Спробуйте ще раз")
        except ValueError:
            await message.answer("Невірний формат дати.Спробуйте ще раз")


async def save_add(message: types.Message, state: FSMContext, kb: InlineKeyboardMarkup):
    text = data.get("adds_text")
    media = data.get("media")
    await Adds.save_add(
        message.message_id,
        bot_id = bot.id,
        adds_text = text,
        delay = data.get('delay') or datetime.datetime.now().replace(microsecond = 0),
        buttons = kb,
        media = await media.get_url() if media else None,
        is_publsihed = False if data.get('delay') else True
    )
    await state.finish()

async def send_add_to_user(user_kb: InlineKeyboardMarkup, add: dict[str]):
    users = await Users.get('bot_id', bot.id, True)
    if users:
        counter = 0
        media = add.get('media')
        text = add.get('adds_text')
        owner_id = (await Bots.get('id', bot.id))['user_id']
        for user in users:
            try:
                channel = user['id']
                if media:
                    file = await fetch_media_bytes(media)
                    if 'photos' in media:
                        await bot.send_photo(channel, file, text, reply_markup = user_kb)
                    elif 'videos' in media:
                        await bot.send_video(channel, file, text, reply_markup = user_kb)
                else:
                    await bot.send_message(channel, text, reply_markup = user_kb)
                counter += 1
            except:
                await bot.send_message(owner_id, f"Відбулася помилка при розисилці", reply_markup = main_menu())
            else:
                await bot.send_message(owner_id, "Розсилка відбулася успішно.Кількість надсилань: <b>{counter}</b>", reply_markup = main_menu(), parse_mode = "html")
    else:
        await bot.send_message(owner_id, "База даних бота пуста.Спробуйте пізніше", reply_markup = main_menu())

async def planned_menue(message: types.Message, state: FSMContext):
    adds = await Adds.get("bot_id", bot.id, True)
    date_format = "%Y-%m-%d %H:%M:%S"

    day = datetime.timedelta(days = 1)
    curr_day = datetime.datetime.now()
    prev_day = (curr_day - day).date()
    next_day = (curr_day + day).date()
    
    if adds:
        today = list(filter(lambda add: add.data.get('delay') and datetime.datetime.strptime(add.data.get('delay'), date_format).date() == prev_day, adds))
        yesterday = list(filter(lambda add: add.data.get('delay') and datetime.datetime.strptime(add.data.get('delay'), date_format).date() == prev_day, adds))
        tomorrow = list(filter(lambda add: add.data.get('delay') and datetime.datetime.strptime(add.data.get('delay'), date_format).date() == next_day, adds))
        date_format = "%H:%M"
        separator = '\n'
        planned_menue_message = f"""
📅 Події

Вчора:
{f"{separator}".join([add['adds_text'] or "" for add in yesterday]) if yesterday else 'пусто'}

Сьогодні:
{f"{separator}".join([add['adds_text'] or "" for add in today]) if today else 'пусто'}

Завтра:
{f"{separator}".join([add['adds_text'] or "" for add in tomorrow]) if tomorrow else 'пусто'}
"""
    await message.answer(planned_menue_message, reply_markup = get_adds_kb()) #reply_markup = get_adds_list_kb()

async def adds_manager():
    date_format = "%Y-%m-%d %H:%M:%S"
    while True:
        adds = await Adds.get("bot_id", bot.id, True)
        if adds:
            for add in adds:
                add_data = add.data 
                is_published = add_data.get('is_published')
                if is_published == False and add_data.get('adds_text'):  
                    delay = add_data.get("delay")
                    if datetime.datetime.strptime(delay, date_format) <= datetime.datetime.now():
                        user_kb = get_user_kb(add_data)
                        await send_add_to_user(user_kb, add_data)
                        await Adds.update("id", add_data["id"], is_published = True)
        await asyncio.sleep(5)

def register_adds(dp: Dispatcher):
    asyncio.get_event_loop().create_task(adds_manager())
    dp.register_message_handler(planned_menue, lambda m: m.text == "Розсилка", IsAdminFilter(), state = "*")
    dp.register_callback_query_handler(process_new_add, lambda cd: cd.data == 'create_add')
    dp.register_callback_query_handler(adds_handler, state = BotAdds.EDITING)
    dp.register_message_handler(edit_adds_text, lambda m: m.text not in ('Розсилка', 'Керувати заявками', 'Привітання', 'Вибрати канал', 'Тарифи'), state = BotAdds.TEXT, content_types = types.ContentTypes.TEXT | types.ContentTypes.PHOTO | types.ContentTypes.VIDEO)
    dp.register_message_handler(edit_adds_media, state = BotAdds.MEDIA, content_types = types.ContentTypes.PHOTO | types.ContentTypes.VIDEO)
    dp.register_message_handler(edit_adds_buttons, state = BotAdds.BTN)
    dp.register_callback_query_handler(choose_date_handler, state = BotAdds.DATE)
    dp.register_message_handler(delay_adds_handler, state = BotAdds.DATE)
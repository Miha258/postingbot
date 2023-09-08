from create_bot import bot, get_channel
import asyncio
from aiogram.utils.exceptions import Unauthorized, MessageCantBeDeleted
from aiogram.utils.callback_data import CallbackData
from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.exceptions import BadRequest
import re
from datetime import datetime
from states import *
from utils import *
from keyboards import *
import calendar


data = {}
posts = {}
months = [
    "Січень", "Лютий", "Березень", "Квітень", "Травень", "Червень",
    "Липень", "Серпень", "Вересень", "Жовтень", "Листопад", "Грудень"
]

def get_kb():
    kb = InlineKeyboardMarkup(inline_keyboard = [
    [
        InlineKeyboardButton("Змінити текст", callback_data = "edit_text"),
        InlineKeyboardButton("Відкріпити медіа", callback_data = "disattach_media") if data.get("media") else InlineKeyboardButton("Прикріпити медіа", callback_data = "attach_media")
    ],
    [
        InlineKeyboardButton("URL-кнопки", callback_data = "url_buttons"),
        InlineKeyboardButton("Парсинг: HTML", callback_data = "markdown") if data.get("parse_mode") == "html" else InlineKeyboardButton("Парсинг: Markdown", callback_data = "html"),
    ],
    [
        InlineKeyboardButton("Увімкнути  коментарі", callback_data = "comments_on") if data["comments"] == "comments_off" else InlineKeyboardButton("Вимкнути коментарі", callback_data = "comments_off")
    ],
    [
        InlineKeyboardButton("🔕", callback_data = "notify_on") if data["notify"] == "notify_off" else InlineKeyboardButton("🔔", callback_data = "notify_off")
    ],
    [
        InlineKeyboardButton("Відкласти", callback_data = "delay_post"),
        InlineKeyboardButton("Опублікувати", callback_data = "create_post")
    ]
    ])
    kb.add(back_btn)
    
    url_buttons = data.get("url_buttons")
    if url_buttons:
        for i, btn in enumerate(url_buttons):
            kb.inline_keyboard.insert(i, [btn])
        kb.inline_keyboard.insert(len(url_buttons), [
            InlineKeyboardButton("Прибрати URL-кнопки", callback_data = "remove_url_buttons")
        ])

    if data.get("hidden_extension_btn"):
        kb.inline_keyboard.insert(len(url_buttons), [
            InlineKeyboardButton("Видалити приховане продовження", callback_data = "hidden_extension_remove")
        ]) 
        kb.inline_keyboard.insert(0, [
            InlineKeyboardButton(data["hidden_extension_btn"], callback_data = "hidden_extension_use")
        ]) 
    else:
        kb.inline_keyboard.insert(1, [
             InlineKeyboardButton("Приховане продовження", callback_data = "hidden_extension")
        ]) 
    
    return kb


async def process_new_post(message: types.Message, state: FSMContext):
    data.clear()
    data["text"] = "Редагуйте текст"
    data["url_buttons"] = []
    data["comments"] = "comments_on"
    data["notify"] = "notify_on"
    data["parse_mode"] = "html"
    data["media"] = None
    await message.answer("Надішліть текст, картику або відео поста")
    await state.set_state(EditStates.EDITING_TEXT)
    

async def edit_post_command(callback_query: types.CallbackQuery, state: FSMContext):
    query = callback_query.data
    message = callback_query.message
    
    match query:
        case "edit_text":
            await state.set_state(EditStates.EDITING_TEXT)
            await message.answer("Введіть новий текст поста:")
        case "attach_media":
            await state.set_state(EditStates.ATTACHING_MEDIA)
            await message.answer("Надішліть мені фото/відео:")
        case "disattach_media":
            await disattaching_media_handler(message, state)      
        case "hidden_extension_remove":
            await remove_hidden_extension(callback_query, state)
        case "hidden_extension":
            await state.set_state(EditStates.HIDDEN_EXTENSION_BTN)
            await message.answer("Введіть назву кнопки з призованим продовженням:")  
        case "comments_off" | "comments_on":
            await comments_handler(callback_query, state)
        case "markdown" | "html":
            await parse_mode_handler(callback_query, state)
        case "url_buttons":
            await state.set_state(EditStates.URL_BUTTONS)
            await message.answer("Введіть текст у форматі: Назва кнопки - посилання") 
        case "remove_url_buttons":
            await remove_url_button_handler(callback_query, state) 
        case "notify_on" | "notify_off":
            await notification_handler(callback_query, state) 
        case "delay_post":      
            await message.answer("Введіть час у форматі і виберіть дату: <b>00:00</b>", parse_mode = "html", reply_markup = get_calendar())    
            await state.set_state(EditStates.DATE)     
        case "create_post":
            await create_post(callback_query.message, state)   
        case "parse_mode":
            await parse_mode_handler(callback_query, state)
        case _:
            return


async def editing_text_handler(message: types.Message, state: FSMContext):
    data["text"] = message.text or message.caption or ""
    media = data.get("media")
    
    kb = get_kb()
    if media:
        if isinstance(media, types.PhotoSize):
            await message.answer_photo(media.file_id, caption = data["text"], parse_mode = data.get("parse_mode"), reply_markup = kb)
        elif isinstance(media, types.Video):
            await message.answer_video(media.file_id, caption = data["text"], parse_mode = data.get("parse_mode"), reply_markup = kb)
    else:
        await message.answer(data["text"], parse_mode = data.get("parse_mode"), reply_markup = kb)
    await state.set_state(BotStates.EDITING_POST)
    

async def attaching_media_handler(message: types.Message, state: FSMContext):
    data["media"] = message.photo[-1] if message.photo else message.video
    
    kb = get_kb()
    media = data.get('media')
    if media:
        if isinstance(media, types.PhotoSize):
            await message.answer_photo(media.file_id, caption = data["text"], parse_mode = data.get("parse_mode"), reply_markup = kb)
        elif isinstance(media, types.Video):
            await message.answer_video(media.file_id, caption = data["text"], parse_mode = data.get("parse_mode"), reply_markup = kb)
    else:
        await message.answer(data["text"], parse_mode = data.get("parse_mode"), reply_markup = kb)
    await state.set_state(BotStates.EDITING_POST)


async def disattaching_media_handler(message: types.Message, state: FSMContext):
    data["media"] = None
    kb = get_kb()
    
    await message.delete()
    await message.answer(data["text"], parse_mode = data.get("parse_mode"), reply_markup = kb)
    await state.set_state(BotStates.EDITING_POST)


async def open_modal(callback_query: types.CallbackQuery):
    message = callback_query.message
    post = posts[message.message_id]

    user_channel_status = await bot.get_chat_member(chat_id = callback_query.message.chat.id, user_id = callback_query.from_user.id)
    if user_channel_status["status"] == "left":
        await callback_query.answer(text = post["hidden_extension_text_1"], show_alert = True)
    else:
        await callback_query.answer(text = post["hidden_extension_text_2"], show_alert = True)


async def remove_hidden_extension(callback_query: types.CallbackQuery, state: FSMContext):
    remove_button_by_callback_data("hidden_extension_use", get_kb())    
    
    del data["hidden_extension_btn"]
    del data["hidden_extension_text_1"]
    del data["hidden_extension_text_2"]
    
    kb = get_kb()
    await callback_query.message.edit_reply_markup(reply_markup = kb)
    await state.set_state(BotStates.EDITING_POST)
    

async def hidden_extension_handler_1(message: types.Message, state: FSMContext):
    data["hidden_extension_btn"] = message.text
  
    await message.answer("Тепер введіть текст, який показується, коли учасник не підписаний на канал:")
    await state.set_state(EditStates.HIDDEN_EXTENSION_TEXT_1)


async def hidden_extension_handler_2(message: types.Message, state: FSMContext):
    data["hidden_extension_text_1"] = message.text
    await message.answer("Тепер введіть текст, який показується, після підписки на канал:")
    await state.set_state(EditStates.HIDDEN_EXTENSION_TEXT_2)


async def init_hidden_extension_handler(message: types.Message, state: FSMContext):
    data["hidden_extension_text_2"] = message.text
    kb = get_kb()
    
    media = data.get('media')
    if media:
        if isinstance(media, types.PhotoSize):
            await message.answer_photo(media.file_id, caption = data["text"], parse_mode = data.get("parse_mode"), reply_markup = kb)
        elif isinstance(media, types.Video):
            await message.answer_video(media.file_id, caption = data["text"], parse_mode = data.get("parse_mode"), reply_markup = kb)
    else:
        await message.answer(data["text"], parse_mode = data.get("parse_mode"), reply_markup = kb)
    await state.set_state(BotStates.EDITING_POST)
    

async def comments_handler(callback_query: types.CallbackQuery, state: FSMContext):
    status = callback_query.data  
    data["comments"] = status
    kb = get_kb()
    await callback_query.message.edit_reply_markup(reply_markup = kb)
    await state.set_state(BotStates.EDITING_POST)
    

async def repost_handler(callback_query: types.Message, state: FSMContext):
    status = callback_query.data  
    data["reposts"] = status
    kb = get_kb()
    await callback_query.message.edit_reply_markup(reply_markup = kb)
    await state.set_state(BotStates.EDITING_POST)


async def parse_mode_handler(callback_query: types.CallbackQuery, state: FSMContext):
    parse_mode = callback_query.data
    data["parse_mode"] = parse_mode
    kb = get_kb()
    await state.set_data({"parse_mode": parse_mode})
    media = data.get('media')
    if media:
        if isinstance(media, types.PhotoSize):
            await callback_query.message.answer_photo(media.file_id, caption = data["text"], parse_mode = data.get("parse_mode"), reply_markup = kb)
        elif isinstance(media, types.Video):
            await callback_query.message.answer_video(media.file_id, caption = data["text"], parse_mode = data.get("parse_mode"), reply_markup = kb)
    else:
        await callback_query.message.answer(data["text"], parse_mode = data.get("parse_mode"), reply_markup = kb)
    await state.set_state(BotStates.EDITING_POST)
    

async def url_button_handler(message: types.Message, state: FSMContext):
    try:
        text = message.text.split(" - ")
        name = text[0]
        url = text[1]
        btn = InlineKeyboardButton(name, url)
        data["url_buttons"].append(btn)
        kb = get_kb()
    except BadRequest:
        await message.answer("Некоректне посилання.Cпробуйте ще раз")
    except IndexError:
        await message.answer("Некоректний формат.Cпробуйте ще раз")
    else:         
        media = data.get('media')
        if media:
            if isinstance(media, types.PhotoSize):
                await message.answer_photo(media.file_id, caption = data["text"], parse_mode = data.get("parse_mode"), reply_markup = kb)
            elif isinstance(media, types.Video):
                await message.answer_video(media.file_id, caption = data["text"], parse_mode = data.get("parse_mode"), reply_markup = kb)
        else:
            await message.answer(data["text"], parse_mode = data.get("parse_mode"), reply_markup = kb)
        await state.set_state(BotStates.EDITING_POST)


async def remove_url_button_handler(callback_query: types.CallbackQuery, state: FSMContext):
    data["url_buttons"].clear()
    kb = get_kb()
    await callback_query.message.edit_reply_markup(reply_markup = kb)
    await state.set_state(BotStates.EDITING_POST)


def get_calendar(month: int = 0):
    inline_markup = types.InlineKeyboardMarkup(row_width=7)
    date = datetime.today()

    if month < 0:
        date = date.replace(year = date.year + 1) 
    
    start = 1 if month else date.day
    end = calendar.monthrange(date.year, date.month + month)[1]
    for day in range(start, end + 1):
        inline_markup.insert(types.InlineKeyboardButton(str(day), callback_data = f"calendar_day:{date.year}-{date.month + month}-{day}"))
    
    inline_markup.row(
        types.InlineKeyboardButton("Назад", callback_data = "prev_month"),
        types.InlineKeyboardButton(months[date.month + month - 1], callback_data = "current_month"),
        types.InlineKeyboardButton("Вперед", callback_data = "next_month"),
    )
    
    return inline_markup


async def set_calendar_month(callback_query: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        index = data.get("calendar") if data.get("calendar") else 0
        add = index + 1 if callback_query.data == "next_month" else index - 1
        data["calendar"] = add
        await callback_query.message.edit_reply_markup(get_calendar(add))
    

async def choose_date_handler(callback_query: types.CallbackQuery, state: FSMContext):
    date = callback_query.data.split(":")[1]
    data['date'] = datetime.strptime(date, "%Y-%m-%d").date()
    await callback_query.answer(f"Ви обрали {date}")


async def delay_post_handler(message: types.Message, state: FSMContext):
    date_time_regex = r'\d{2}:\d{2}'
    date_string = message.text
    date = data.get("date")
    
    if not date:
        return await message.answer("Ви не вибрали дату")

    if re.search(date_time_regex, date_string):
        time = datetime.strptime(date_string, "%H:%M").time()
        date = datetime.combine(date, time)
        if date <= datetime.now():
            await message.answer(f"Недійсна дата.Спробуйте ще раз")  
            return
        
        data["delay"] = date
        data["delay_str"] = date_string
        await create_post(message, state)
        await state.set_state(BotStates.EDITING_POST)
    else:
        await message.answer("Невірний формат дати.Спробуйте ще раз")


async def send_post(message: types.Message, user_kb: InlineKeyboardMarkup):
    try:
        data = posts[message.message_id]
        channel = get_channel()
        media = data.get('media')
        disable_notification = True if data["notify"] == "notify_off" else False
        if media:
            if isinstance(media, types.PhotoSize):
                post = await bot.send_photo(channel, media.file_id, caption = data["text"], parse_mode = data.get("parse_mode"), reply_markup = user_kb, disable_notification = disable_notification)
            elif isinstance(media, types.Video):
                post = await message.send_photo(channel, media.file_id, caption = data["text"], parse_mode = data.get("parse_mode"), reply_markup = user_kb, disable_notification = disable_notification)
        else:
            post = await bot.send_message(channel, data["text"], parse_mode = data.get("parse_mode"), reply_markup = user_kb, disable_notification = disable_notification)
        
        if data.get("comments") == "comments_off":
            await asyncio.sleep(5)
            chat_url = (await bot.get_chat(channel)).linked_chat_id
            chat = await bot.get_chat(chat_url)
            await chat.pinned_message.delete()

        del posts[message.message_id]
        posts[post.message_id] = data
        return post 
    
    except MessageCantBeDeleted:
        await message.answer("Зробіть мене адміністратором бесіди каналу")
    except Unauthorized:
        await message.answer("Щоб вимкнути коментарі - додайте мене у бесіду каналу")
    except Exception:
        await message.answer("Під час відправлення у ваш канал поста виникла помилка!Спробуйте ще раз")


async def send_post_with_delay(message: types.Message, delay: int, user_kb: InlineKeyboardMarkup):
    while datetime.now() < delay:
        await asyncio.sleep(3)
    post = await send_post(message, user_kb, message.message_id)
    await message.edit_text(f'<b><a href="{post.url}">Пост</a> успішно опублікований!</b>', parse_mode = 'html')


async def create_post(message: types.Message, state: FSMContext):
    user_kb = InlineKeyboardMarkup()

    if data.get("hidden_extension_btn"):
        user_kb.add(InlineKeyboardButton(data["hidden_extension_btn"], callback_data="hidden_extension_use"))

    if data.get("url_buttons"):
        user_kb.add(*data["url_buttons"])

    user_kb = user_kb if user_kb.inline_keyboard else None
    date = data.get("delay_str")
    delay = data.get("delay")

    await state.finish()
    posts[message.message_id] = data.copy()
    

    if date and delay:
        await message.answer(f"Пост буде опубліковано: <b>{date} {data['date']}</b>", parse_mode = "html")
        asyncio.create_task(send_post_with_delay(message, delay, user_kb))
    else:
        post = await send_post(message, user_kb)
        await message.answer(f'<b><a href="{post.url}">Пост</a> успішно опублікований!</b>', parse_mode = 'html')
    data.clear()

async def notification_handler(callback_query: types.CallbackQuery, state: FSMContext):
    status = callback_query.data  
    
    data["notify"] = status
    kb = get_kb()
    await callback_query.message.edit_reply_markup(reply_markup = kb)
    await state.set_state(BotStates.EDITING_POST)

    
def register_posting(dp: Dispatcher):
    dp.register_callback_query_handler(edit_post_command, state = BotStates.EDITING_POST)
    dp.register_message_handler(url_button_handler, state = EditStates.URL_BUTTONS)
    dp.register_message_handler(editing_text_handler, state = EditStates.EDITING_TEXT, content_types = [types.ContentType.TEXT, types.ContentType.VIDEO, types.ContentType.PHOTO])
    dp.register_message_handler(attaching_media_handler, state = EditStates.ATTACHING_MEDIA, content_types=[types.ContentType.PHOTO, types.ContentType.VIDEO])
    dp.register_callback_query_handler(open_modal, lambda cb: CallbackData("hidden_extension_use").filter() and cb.message.message_id in posts.keys())
    dp.register_message_handler(hidden_extension_handler_1, state = EditStates.HIDDEN_EXTENSION_BTN)
    dp.register_message_handler(hidden_extension_handler_2, state = EditStates.HIDDEN_EXTENSION_TEXT_1)
    dp.register_message_handler(init_hidden_extension_handler, state = EditStates.HIDDEN_EXTENSION_TEXT_2)
    dp.register_callback_query_handler(parse_mode_handler, state = EditStates.PARSE_MODE)
    dp.register_message_handler(delay_post_handler, state = EditStates.DATE) 
    dp.register_callback_query_handler(choose_date_handler, lambda cb: "calendar_day" in cb.data, state = EditStates.DATE)
    dp.register_callback_query_handler(set_calendar_month, lambda cb: cb.data in ["prev_month", "next_month"], state = EditStates.DATE)
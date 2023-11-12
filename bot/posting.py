from create_bot import bot, get_channel
import asyncio
from aiogram.utils.exceptions import Unauthorized, FileIsTooBig, MessageToEditNotFound
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
from db.account import Posts, Channels

data = {}
preview = True
def get_kb():
    watermark = data.get('watermark')
    if watermark:
        watermark = re.search(r'<a.*?>(.*?)</a>', watermark) or re.search(r'\[([^\]]+)\]\([^)]+\)', watermark)
        if watermark:
            watermark = watermark.group(1)
    kb = InlineKeyboardMarkup(inline_keyboard = [
    [
        InlineKeyboardButton("Змінити текст", callback_data = "edit_text"),
        InlineKeyboardButton("Відкріпити медіа", callback_data = "disattach_media") if data.get("media") else InlineKeyboardButton("Прикріпити медіа", callback_data = "attach_media")
        
    ],
    [
        InlineKeyboardButton("URL-кнопки", callback_data = "url_buttons"),
        InlineKeyboardButton("Парсинг: HTML", callback_data = "markdown") if data.get("parse_mode") == types.ParseMode.HTML else InlineKeyboardButton("Парсинг: Markdown", callback_data = "html"),
    ],
    [
        InlineKeyboardButton("Увімкнути  коментарі", callback_data = "comments_on") if not data["comments"] else InlineKeyboardButton("Вимкнути коментарі", callback_data = "comments_off")
    ],
    [
        InlineKeyboardButton("Додати автопідпис", callback_data = "watermark_on") if not watermark else InlineKeyboardButton(f"Прибрати автопідпис ({watermark})", callback_data = "watermark_off")
    ],
    [  
        InlineKeyboardButton("Автовидалення", callback_data = "autodelete_on") if not data["autodelete"] else InlineKeyboardButton(f"Прибрати автовидалення ({round((data.get('autodelete') - datetime.datetime.now()).total_seconds() / 3600)}h)", callback_data = "autodelete_off")
    ],
    [  
        InlineKeyboardButton("Превю: вкл", callback_data = "set_preview") if preview else InlineKeyboardButton(f"Превю: викл", callback_data = "set_preview")
    ],
    [InlineKeyboardButton("Відредагувати", callback_data = "change_post_data")] if data.get('is_editing') else [
        InlineKeyboardButton("Відкласти", callback_data = "delay_post"),
        InlineKeyboardButton("Опублікувати", callback_data = "create_post")
    ]
    ])
    kb.add(back_btn)

    if data.get('datetime'):
        remove_button_by_callback_data('create_post', kb)
    
    if not data.get('is_editing'):
        kb.inline_keyboard.insert(len(kb.inline_keyboard) - 1,[
            InlineKeyboardButton(
                "🔕", 
                callback_data = "notify_on"
        ) if not data["notify"] else 
            InlineKeyboardButton(
                "🔔", 
                callback_data = "notify_off"
        )])
    
    if data.get('is_editing'):
        remove_button_by_callback_data("watermark_off", kb)
        remove_button_by_callback_data("comments_on", kb)
        remove_button_by_callback_data("comments_off", kb)
        if not data.get('media'):
            remove_button_by_callback_data("disattach_media", kb)
            kb.inline_keyboard.insert(0, [InlineKeyboardButton("Замінити медіа", callback_data = "attach_media")])
    
    url_buttons = data.get("url_buttons")
    if preview:
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
        
    if data.get("hidden_extension_btn"):
        kb.inline_keyboard.insert(len(url_buttons), [
            InlineKeyboardButton("Видалити приховане продовження", callback_data = "hidden_extension_remove")
        ]) 
        if preview:
            kb.inline_keyboard.insert(len(url_buttons), [
                InlineKeyboardButton(data["hidden_extension_btn"], callback_data = "hidden_extension_use")
            ]) 
    else:
        kb.inline_keyboard.insert(len(url_buttons),  [
             InlineKeyboardButton("Приховане продовження", callback_data = "hidden_extension")
        ]) 
    return kb


async def process_new_post(message: types.Message, state: FSMContext):
    data.clear()
    data["text"] = None
    data["watermark"] = (await Channels.get('chat_id', get_channel()))['watermark']
    data["comments"] = False
    data["notify"] = False
    data["url_buttons"] = []
    data["parse_mode"] = types.ParseMode.HTML
    data["media"] = None
    data["autodelete"] = None
    data["datetime"] = (await state.get_data()).get('datetime')
    await message.answer("Надішліть текст, картику або відео поста")
    await state.set_state(EditStates.EDITING_TEXT)
    

async def edit_post_command(callback_query: types.CallbackQuery, state: FSMContext):
    query = callback_query.data
    message = callback_query.message
    
    match query:
        case "edit_text":
            await state.set_state(EditStates.EDITING_TEXT)
            await message.answer("Введіть новий текст поста:", reply_markup = back_to_edit)
        case "attach_media":
            await state.set_state(EditStates.ATTACHING_MEDIA)
            await message.answer("Надішліть мені фото/відео:")
        case "disattach_media":
            await disattaching_media_handler(message, state)      
        case "hidden_extension_remove":
            await remove_hidden_extension(callback_query, state)
        case "hidden_extension":
            await state.set_state(EditStates.HIDDEN_EXTENSION_BTN)
            await message.answer("Введіть назву кнопки з прихованим продовженням:", reply_markup = back_to_edit)  
        case "watermark_on":
            await state.set_state(EditStates.WATERMARK_TEXT)
            await message.answer('Введіть текст з посиланням (<a href="https://example.com/">Підписатися на канал</a>):', reply_markup = back_to_edit, parse_mode = types.ParseMode.HTML)  
        case "watermark_off":
            await remove_watermark_handler(callback_query, state)
        case "autodelete_on":
            await state.set_state(EditStates.AUTODELETE)
            await message.answer("Виберіть, через скільки часу мені видалити пост:", reply_markup = get_autodelete_kb().add(back_to_edit.inline_keyboard[0][0]))  
        case "autodelete_off":
            await remove_autodelete_handler(callback_query, state)
        case "comments_off" | "comments_on":
            await comments_handler(callback_query, state)
        case "markdown" | "html":
            await parse_mode_handler(callback_query, state)
        case "url_buttons":
            await state.set_state(EditStates.URL_BUTTONS)
            await message.answer("Введіть кнопку у форматі: \n<em>1. Кнопка - посилання</em>\n<em>2. Кнопка - посилання</em>\n<em>3. Кнопка - посилання</em>\n\n<strong>Використовуйте | щоб кнопки поставити кнопки в один рядок:</strong>\n\n<em>1. Кнопка - посилання | Кнопка - посилання</em>\n<em>2. Кнопка - посилання | Кнопка - посилання</em>\n<em>3. Кнопка - посилання | Кнопка - посилання</em>", parse_mode = "html")
        case "remove_url_buttons":
            await remove_url_button_handler(callback_query, state) 
        case "notify_on" | "notify_off":
            await notification_handler(callback_query, state) 
        case "delay_post": 
            await state.set_state(EditStates.DATE)    
            date_time = data.get("datetime")
            if date_time:
                await delay_post_handler(message, state)
            else:
                await message.answer("Введіть час у форматі і виберіть дату: <b>00:00</b>", parse_mode = "html", reply_markup = get_calendar().add(back_to_edit.inline_keyboard[0][0]))     
        case "create_post":
            await state.set_state(EditStates.COMFIRM)
            await message.answer('Підтвердіть публікацію:', reply_markup = confirm_post_kb)  
        case "parse_mode":
            await parse_mode_handler(callback_query, state)
        case _:
            return

async def editing_text_handler(message: types.Message, state: FSMContext):
    if not data["text"] and not data["media"]:
        data["media"] = message.photo[-1] if message.photo else message.video
    if not data["url_buttons"] and message.reply_markup:
        data["url_buttons"] = message.reply_markup.inline_keyboard
    
    if message.text or message.caption:
        data["text"] = message.md_text or message.caption if data.get("parse_mode") == types.ParseMode.MARKDOWN else message.html_text or message.caption
    else:
        data["media"] = message.photo[-1] if message.photo else message.video
        return await message.answer('Тепер введіть текст поста:')
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


async def set_preview(callback_query: types.CallbackQuery):
    global preview
    if preview:
        preview = False
    else:
        preview = True
    kb = get_kb()
    await callback_query.message.edit_reply_markup(reply_markup = kb)


async def disattaching_media_handler(message: types.Message, state: FSMContext):
    data["media"] = None
    kb = get_kb()
    
    await message.delete()
    await message.answer(data["text"], parse_mode = data.get("parse_mode"), reply_markup = kb)
    await state.set_state(BotStates.EDITING_POST)


async def open_modal(callback_query: types.CallbackQuery):
    message = callback_query.message
    post = await Posts.get("id", message.message_id)

    if post:
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
    data["comments"] = not data["comments"]
    kb = get_kb()
    await callback_query.message.edit_reply_markup(reply_markup = kb)
    await state.set_state(BotStates.EDITING_POST)


async def add_watermark_handler(message: types.Message, state: FSMContext):
    data["watermark"] = message.md_text if data.get('parse_mode') == types.ParseMode.MARKDOWN else message.html_text
    id = (await Channels.get('chat_id', get_channel()))["id"]
    await Channels.update("id", id, watermark = data["watermark"])
    
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


async def remove_watermark_handler(callback_query: types.CallbackQuery, state: FSMContext):  
    data["watermark"] = None
    kb = get_kb()
    await callback_query.message.edit_reply_markup(reply_markup = kb)
    await state.set_state(BotStates.EDITING_POST)


async def set_autodelete_handler(callback_query: types.CallbackQuery, state: FSMContext):  
    autodelete = datetime.datetime.now() + datetime.timedelta(hours = int(callback_query.data.split('_')[-1]))
    autodelete = autodelete.replace(microsecond = 0)
    data['autodelete'] = autodelete
    message = callback_query.message
    kb = get_kb()
    media = data.get('media')
    if media:
        if isinstance(media, types.PhotoSize):
            await message.answer_photo( media.file_id, caption = data["text"], parse_mode = data.get("parse_mode"), reply_markup = kb)
        elif isinstance(media, types.Video):
            await message.answer_video(media.file_id, caption = data["text"], parse_mode = data.get("parse_mode"), reply_markup = kb)
    else:
        await message.answer(data["text"], parse_mode = data.get("parse_mode"), reply_markup = kb)
    await state.set_state(BotStates.EDITING_POST)


async def remove_autodelete_handler(callback_query: types.CallbackQuery, state: FSMContext):  
    data["autodelete"] = None
    kb = get_kb()
    await callback_query.message.edit_reply_markup(reply_markup = kb)
    await state.set_state(BotStates.EDITING_POST) 


async def repost_handler(callback_query: types.Message, state: FSMContext):
    data["reposts"] = not data["reposts"]
    kb = get_kb()
    await callback_query.message.edit_reply_markup(reply_markup = kb)
    await state.set_state(BotStates.EDITING_POST)


async def parse_mode_handler(callback_query: types.CallbackQuery, state: FSMContext):
    parse_mode = callback_query.data
    data["parse_mode"] = types.ParseMode.HTML if parse_mode == 'html' else types.ParseMode.MARKDOWN
    await state.set_data({"parse_mode": parse_mode})
    kb = get_kb()
    await callback_query.message.edit_reply_markup(kb)
    await state.set_state(BotStates.EDITING_POST)
    

async def url_button_handler(message: types.Message, state: FSMContext):
    try:
        matches = message.text.split('\n')
        kb = None
        if matches:
            kb = types.InlineKeyboardMarkup(row_width = 1)
            for btn in matches:
                if '|' in btn:
                    rows = btn.split(' | ')
                    data["url_buttons"].append([InlineKeyboardButton(row.split(' - ')[0], row.split(' - ')[1]) for row in rows])
                else:
                    column_buttons = btn.split(' - ')
                    if len(column_buttons) > 1:
                        name, url = column_buttons
                        data["url_buttons"].append([InlineKeyboardButton(name, url)])

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
    except BadRequest:
        await message.answer("Некоректне посилання.Cпробуйте ще раз")
    except IndexError:
        await message.answer("Некоректний формат.Cпробуйте ще раз")
    except ValueError:
        await message.answer("Некоректний формат.Cпробуйте ще раз")

async def remove_url_button_handler(callback_query: types.CallbackQuery, state: FSMContext):
    data["url_buttons"].clear()
    kb = get_kb()
    await callback_query.message.edit_reply_markup(reply_markup = kb)
    await state.set_state(BotStates.EDITING_POST)


async def set_calendar_month(callback_query: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        index = data.get("calendar") if data.get("calendar") else 0
        add = index + 1 if callback_query.data == "next_month" else index - 1
        data["calendar"] = add
        await callback_query.message.edit_reply_markup(get_calendar(add))
    

async def choose_date_handler(callback_query: types.CallbackQuery):
    date = callback_query.data.split(":")[1]
    data['date'] = datetime.datetime.strptime(date, "%Y-%m-%d").date()
    await callback_query.answer(f"Ви обрали {date}")
    

async def delay_post_handler(message: types.Message, state: FSMContext):
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
                data["delay_str"] = date_string
                await state.set_state(EditStates.COMFIRM)
                await message.answer("Виберіть дію:", reply_markup = confirm_deley_post_kb)
            else:                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  
                await message.answer("Невірний формат дати.Спробуйте ще раз")
        except ValueError:
            await message.answer("Невірний формат дати.Спробуйте ще раз")


async def comfirm_delay_post(callback_query: types.CallbackQuery, state: FSMContext):
    try:
        message = callback_query.message
        media = data.get('media')
        date = data.get("datetime") or data.get('delay')
        await Posts.save_post(
            message.message_id, 
            bot.id,
            get_channel(),
            data.get('text'),
            data.get("hidden_extension_text_1"),
            data.get("hidden_extension_text_2"),
            data.get("hidden_extension_btn"),
            data.get("url_buttons"),
            data.get("parse_mode"),
            data.get('comments'),
            data.get('watermark'),
            data.get('notify'),
            date,
            await media.get_url() if media else None,
            data.get('autodelete')
        )
        data.clear()
        await message.answer(f"Пост буде опубліковано: <b>{date}</b>", parse_mode = "html", reply_markup = make_new_post_kb)
        await state.finish()
    except FileIsTooBig:
        await message.answer("Файл завеликий, спробуйте ще раз:")


async def send_post(user_kb: InlineKeyboardMarkup, channel: str = None, _data: dict = None) -> types.Message:
    global data
    channel = channel or get_channel()
    
    data = _data if _data else data
    media = data.get('media')
    disable_notification = not data.get("notify")
    text = data.get('text') or data.get('post_text')
    parse_mode = data.get("parse_mode")
    watermark = data.get('watermark')
    if watermark:
        text += "\n\n" + watermark
    
    if media:
        if isinstance(media, types.PhotoSize):
            post = await bot.send_photo(channel, media.file_id, caption = text, parse_mode = parse_mode, reply_markup = user_kb, disable_notification = disable_notification)
        elif isinstance(media, types.Video):
            post = await bot.send_video(channel, media.file_id, caption = text, parse_mode = parse_mode, reply_markup = user_kb, disable_notification = disable_notification) 
        elif isinstance(media, str):
            file = await fetch_media_bytes(media)
            is_video = types.InputMediaVideo(file).duration
            if is_video:
                post = await bot.send_video(channel, file, caption = text, parse_mode = parse_mode, reply_markup = user_kb, disable_notification = disable_notification) 
            elif not is_video:
                post = await bot.send_photo(channel, file, caption = text, parse_mode = parse_mode, reply_markup = user_kb, disable_notification = disable_notification)
    else:
        post = await bot.send_message(channel, text, parse_mode = parse_mode, reply_markup = user_kb, disable_notification = disable_notification)
    
    if data.get("comments"):
        await asyncio.sleep(5)
        chat_url = (await bot.get_chat(channel)).linked_chat_id
        chat = await bot.get_chat(chat_url)
        await chat.pinned_message.delete()
    return post 
    

async def cancle_post(callback_query: types.CallbackQuery, state: FSMContext):
    kb = get_kb()

    message = callback_query.message
    media = data.get('media')
    if media:
        if isinstance(media, types.PhotoSize):
            await message.answer_photo(media.file_id, caption = data["text"], parse_mode = data.get("parse_mode"), reply_markup = kb)
        elif isinstance(media, types.Video):
            await message.answer_video(media.file_id, caption = data["text"], parse_mode = data.get("parse_mode"), reply_markup = kb)
    else:
        await message.answer(data["text"], parse_mode = data.get("parse_mode"), reply_markup = kb)
    await state.set_state(BotStates.EDITING_POST)


async def create_post(callback_query: types.CallbackQuery, state: FSMContext):
    user_kb = get_user_kb(data)
    message = callback_query.message
    channel = get_channel()
    post = await send_post(user_kb)
    media = data.get('media')
    await message.answer(f'<b><a href="{post.url}">Пост</a> успішно опублікований!</b>', parse_mode = 'html', reply_markup = make_new_post_kb)
    await Posts.save_post(
        post.message_id,
        bot.id,
        channel,
        data.get('text'),
        data.get("hidden_extension_text_1"),
        data.get("hidden_extension_text_2"),
        data.get("hidden_extension_btn"),
        data.get("url_buttons"),
        data.get("parse_mode"),
        data.get('comments'),
        data.get('notify'),
        data.get('watermark'),
        data.get('delay'),
        await media.get_url() if media else None,
        data.get('autodelete')
    )
    data.clear()
    await state.finish()


async def notification_handler(callback_query: types.CallbackQuery, state: FSMContext):
    data["notify"] = not data["notify"]
    kb = get_kb()
    await callback_query.message.edit_reply_markup(reply_markup = kb)
    await state.set_state(BotStates.EDITING_POST)


async def back_to_editing(callback_query: types.CallbackQuery, state: FSMContext):
    media = data.get("media")
    kb = get_kb()
    if media: 
        await callback_query.message.delete()
        if isinstance(media, types.PhotoSize):
            await callback_query.message.answer_photo(media.file_id, caption = data["text"], parse_mode = data.get("parse_mode"), reply_markup = kb)
        elif isinstance(media, types.Video):
            await callback_query.message.answer_video(media.file_id, caption = data["text"], parse_mode = data.get("parse_mode"), reply_markup = kb)
    else:
        await callback_query.message.edit_text(data["text"], parse_mode = data.get("parse_mode"), reply_markup = kb)
    await state.set_state(BotStates.EDITING_POST)


async def create_post_again(callback_query: types.CallbackQuery, state: FSMContext):
    await process_new_post(callback_query.message, state)
    

async def choose_post_for_edit(message: types.Message, state: FSMContext):
    await state.set_state(BotStates.CHANGE_POST)
    await message.answer('Перешліть мені пост, який бажаєте відредагувати:', reply_markup = back_to_menu())


async def edit_post(message: types.Message, state: FSMContext, post_id = None | int):
    global data
    target_message = post_id or message.forward_from_message_id
    post = await Posts.get('id', target_message)
    if not post:
        return await message.answer('Пост не знайдено.Спробуйте інший:')

    data = post.to_dict()
    if data:
        data['is_editing'] = True
        data['text'] = data['post_text']
        data['media'] = message.photo[-1] if message.photo else message.video
        data['watermark'] = (await Channels.get('chat_id', post["channel_id"]))['watermark']
        url_buttons = []

        for btn in data.get('url_buttons').split('\n'):
            if '|' in btn:
                rows = btn.split(' | ')
                row_buttons = []
                for row in rows:
                    name, url = row.split(' - ')
                    row_buttons.append(InlineKeyboardButton(name, url))
                url_buttons.append(row_buttons)
            else:
                column_buttons = btn.split(' - ')
                if len(column_buttons) > 1:
                    name, url = column_buttons
                    url_buttons.append([InlineKeyboardButton(name, url)])

        data['url_buttons'] = url_buttons
        kb = get_kb()   

        await state.set_state(BotStates.EDITING_POST)
        if post_id:
            await message.edit_reply_markup(kb)
        else:
            media = data['media']
            if media:
                if isinstance(media, types.PhotoSize):
                    await message.answer_photo(media.file_id, caption = data["text"], parse_mode = data.get("parse_mode"), reply_markup = kb)
                elif isinstance(media, types.Video):
                    await message.answer_video(media.file_id, caption = data["text"], parse_mode = data.get("parse_mode"), reply_markup = kb)
            else:
                await message.answer(data["post_text"], parse_mode = data.get("parse_mode"), reply_markup = kb)
    else:
        await message.answer('Цей пост не знайдений, спробуйте інший')

async def change_post_data(callback_query: types.CallbackQuery, state: FSMContext):
    message = callback_query.message

    post = await Posts.get('id', data.get('id'))
    channel_id = post['channel_id']
    post_id = post['id']
    media = data.get('media')
    user_kb = get_user_kb(data)
    
    text = data['text']
    watermark = data.get('watermark')
    if watermark:
        text += "\n\n" + watermark 
    try:
        is_posted = True
        try:
            if media:
                media_file_id = media.file_id
                input_media = None
                if isinstance(media, types.PhotoSize):
                    input_media = types.InputMediaPhoto(media_file_id, text, parse_mode = data.get('parse_mode'))
                elif isinstance(media, types.Video):
                    input_media = types.InputMediaVideo(media_file_id, text, parse_mode = data.get('parse_mode'))
                
                post = await bot.edit_message_media(chat_id = channel_id, message_id = post_id, media = input_media, reply_markup = user_kb)
            else:
                post = await bot.edit_message_text(chat_id = channel_id, message_id = post_id, text = text, reply_markup = user_kb, parse_mode = data.get('parse_mode'))
        except MessageToEditNotFound:
            is_posted = False
            
        if data.get("comments"):
            await asyncio.sleep(5)
            chat_url = (await bot.get_chat(post_id)).linked_chat_id
            chat = await bot.get_chat(chat_url)
            await chat.pinned_message.delete()
        
        await Posts.edit_post(
            post_id,
            data.get("text"),
            data.get("hidden_extension_text_1"),
            data.get("hidden_extension_text_2"),
            data.get("hidden_extension_btn"),
            data.get("url_buttons"),
            data.get("parse_mode"),
            data.get("comments"),
            data.get("notify"),
            data.get("watermark"),
            await media.get_url() if media else None,
            data.get('autodelete')
        )
        if is_posted:
            await callback_query.message.answer(f'<b><a href="{post.url}">Пост</a> успішно відредаговано</b>', parse_mode = "html")
        else:
            await callback_query.message.answer('Пост відредаговано')
        await state.finish()

    except Unauthorized:
        await message.answer("Щоб вимкнути коментарі - додайте мене у бесіду каналу")
            
async def post_manager():
    date_format = "%Y-%m-%d %H:%M:%S"
    while True:
        posts = await Posts.get("bot_id", bot.id, True)
        if posts:
            for post in posts:
                post_data = post.data 
                delay = post_data.get("delay")
                autodelete = post_data.get('autodelete')
                if delay:  
                    if datetime.datetime.strptime(delay, date_format) <= datetime.datetime.now():
                        user_kb = get_user_kb(post_data)
                        msg = await send_post(user_kb, post_data["channel_id"], post_data)
                        await Posts.update("id", post_data["id"], delay = None, id = msg.message_id)
                if autodelete:
                    if datetime.datetime.strptime(autodelete, date_format) <= datetime.datetime.now():
                        await bot.delete_message(post_data["channel_id"], post_data["id"])
                        await Posts.delete(post_data["id"])
        await asyncio.sleep(5)

def register_posting(dp: Dispatcher):
    asyncio.get_event_loop().create_task(post_manager())
    dp.register_message_handler(process_new_post, lambda m: m.text == 'Постинг', IsAdminFilter(), IsChannel(), state = "*")
    dp.register_callback_query_handler(set_preview, lambda cb: cb.data == 'set_preview', state = "*")
    dp.register_callback_query_handler(back_to_editing, lambda cb: "back_to_edit" == cb.data, state = "*")
    dp.register_message_handler(choose_post_for_edit, lambda m: m.text == 'Редагувати пост', IsAdminFilter(), state = '*')
    dp.register_message_handler(edit_post, state = BotStates.CHANGE_POST, content_types = [types.ContentType.TEXT, types.ContentType.VIDEO, types.ContentType.PHOTO])
    dp.register_callback_query_handler(change_post_data, lambda cb: "change_post_data" in cb.data, state = BotStates.EDITING_POST)
    dp.register_callback_query_handler(edit_post_command, state = BotStates.EDITING_POST)
    dp.register_message_handler(url_button_handler, state = EditStates.URL_BUTTONS)
    dp.register_message_handler(editing_text_handler, state = EditStates.EDITING_TEXT, content_types = [types.ContentType.TEXT, types.ContentType.VIDEO, types.ContentType.PHOTO])
    dp.register_message_handler(attaching_media_handler, state = EditStates.ATTACHING_MEDIA, content_types=[types.ContentType.PHOTO, types.ContentType.VIDEO])
    dp.register_callback_query_handler(open_modal, CallbackData("hidden_extension_use").filter())
    dp.register_message_handler(hidden_extension_handler_1, state = EditStates.HIDDEN_EXTENSION_BTN)
    dp.register_message_handler(hidden_extension_handler_2, state = EditStates.HIDDEN_EXTENSION_TEXT_1)
    dp.register_message_handler(init_hidden_extension_handler, state = EditStates.HIDDEN_EXTENSION_TEXT_2)
    dp.register_message_handler(add_watermark_handler, state = EditStates.WATERMARK_TEXT)
    dp.register_callback_query_handler(set_autodelete_handler, state = EditStates.AUTODELETE)
    dp.register_callback_query_handler(parse_mode_handler, state = EditStates.PARSE_MODE)
    dp.register_message_handler(delay_post_handler, state = EditStates.DATE)
    dp.register_callback_query_handler(comfirm_delay_post, lambda cb: cb.data == "delay_post", state = EditStates.COMFIRM)
    dp.register_callback_query_handler(choose_date_handler, lambda cb: "calendar_day" in cb.data, state = EditStates.DATE)
    dp.register_callback_query_handler(set_calendar_month, lambda cb: cb.data in ("prev_month", "next_month"), state = EditStates.DATE)
    dp.register_callback_query_handler(cancle_post, lambda cb: "cancle_post" == cb.data, state = EditStates.COMFIRM)
    dp.register_callback_query_handler(create_post, lambda cb: "create_post" == cb.data, state = EditStates.COMFIRM)
    dp.register_callback_query_handler(create_post_again, lambda cb: "create_post_again" == cb.data)
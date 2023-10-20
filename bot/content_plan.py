from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from db.account import Posts
from create_bot import get_channel
from datetime import timedelta
from states import ContentPlan
from posting import process_new_post
from keyboards import *
from re import search
from utils import fetch_media_bytes

async def get_plan_kb(date: datetime.datetime, full = False):
    posts = await Posts.get('channel_id', get_channel(), True)
    kb = InlineKeyboardMarkup()
    if posts:
        for post in posts:
            if post['delay']:
                delay = datetime.datetime.strptime(post['delay'], "%Y-%m-%d %H:%M:%S")
                if delay.date() == date.date():
                    kb.add(InlineKeyboardButton(
                        f"📅 {post['delay']}",
                        callback_data = f'edit_planed_post_{post["id"]}'
                    )
            )
                    
    if full:
        return get_calendar()  
        
    date_fromat = "%Y-%m-%d"
    plus_day = timedelta(days = 1)

    prev_day = datetime.datetime.strftime(date - plus_day, date_fromat)
    curr_day = datetime.datetime.strftime(date, date_fromat)
    next_day = datetime.datetime.strftime(date + plus_day, date_fromat)
    
    day_buttons = []
    if (date - plus_day).date() >= datetime.datetime.now().date():
        day_buttons.append(
            InlineKeyboardButton(
                f"← {prev_day}",
                callback_data = f'prev_day'
            )
        )
    day_buttons.append(
        InlineKeyboardButton(
            f"{curr_day}",
            callback_data = f'_'
        )
    )
    day_buttons.append(
        InlineKeyboardButton(
            f"{next_day} →",
            callback_data = f'next_day'
        )
    )
    kb.inline_keyboard.append(day_buttons)
    kb.add(
        InlineKeyboardButton(
            f"Розгорнути календар",
            callback_data = f'full_calendar'
        )
    )
    kb.add(
        InlineKeyboardButton(
            f"Запланувати пост",
            callback_data = f'plan_post'
        )
    )
    return kb

async def plan_post(callback_query: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        data['date'] = (datetime.datetime.now() + timedelta(data['date_offset'])).date()
        message = callback_query.message
        await message.delete_reply_markup()
        await message.edit_text("Введіть час у форматі: <b>00:00</b>", parse_mode = "html")
        await state.set_state(ContentPlan.CHOOSE_DATE)

async def choose_plan_post_time(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        date_time_regex = r'\d{2}:\d{2}'
        date_string = message.text
        date = data["date"]
        
    if search(date_time_regex, date_string):
        time = datetime.datetime.strptime(date_string, "%H:%M").time()
        date_time = datetime.datetime.combine(date, time)
        if date_time <= datetime.datetime.now():
            return await message.answer(f"Недійсна дата.Спробуйте ще раз")  
        await state.update_data({'datetime': date_time})
        await process_new_post(message, state)
    else:
        await message.answer("Невірний формат дати.Спробуйте ще раз")


async def set_day(callback_query: types.CallbackQuery, state: FSMContext):
    plus_or_minus = callback_query.data

    async with state.proxy() as data:
        match plus_or_minus:
            case "prev_day": 
                data['date_offset'] = data['date_offset'] - 1
            case "next_day":
                data['date_offset'] = data['date_offset'] + 1
        date = datetime.datetime.now() + timedelta(data['date_offset'])
        await callback_query.message.edit_reply_markup(
            await get_plan_kb(date)
        )


async def set_full_calendar_day(callback_query: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        date = callback_query.data.split(":")[1]
        date = datetime.datetime.strptime(date, "%Y-%m-%d")
        await state.update_data({"date": date})
        if data.get('post_id'):
            await callback_query.answer(f'Ви вибрали: {date.strftime("%Y-%m-%d")}')
        else:
            await callback_query.message.edit_reply_markup(await get_plan_kb(date))
            await state.set_state(ContentPlan.CHOOSE_DAY)

async def set_full_calendar_month(callback_query: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        index = data.get("calendar") if data.get("calendar") else 0
        add = index + 1 if callback_query.data == "next_month" else index - 1
        data["calendar"] = add
        await callback_query.message.edit_reply_markup(get_calendar(add))


async def content_plan_list(message: types.Message, state: FSMContext):
    date = datetime.datetime.now()
    await message.answer('У цьому розділі ви можете переглядати та редагувати всі заплановані публікації у своїх проектах. Виберіть канал для перегляду контент-плану:',
    reply_markup = await get_plan_kb(date))
    await state.set_data({'date_offset': 0})
    await state.set_state(ContentPlan.CHOOSE_DAY)

async def set_calendar_state(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.message.edit_reply_markup(await get_plan_kb(datetime.datetime.now(), True))
    await state.set_state(ContentPlan.DATE)

async def edit_planed_post(callback_query: types.CallbackQuery):
    post_id = int(callback_query.data.split('_')[-1])
    post = await Posts.get('id', post_id)
    message = callback_query.message
    
    media = post['media']
    if media:
        file = await fetch_media_bytes(media)
        is_video = types.InputMediaVideo(file).duration
        if is_video:
            post = await message.answer_video(file, caption = post['post_text'], parse_mode = post["parse_mode"]) 
        elif not is_video:
            post = await message.answer_photo(file, caption = post['post_text'], parse_mode = post["parse_mode"])
    else:
        await message.answer(post['post_text'], reply_markup = get_edit_planed_post_kb(post_id))
    await message.delete()

async def handle_planed_post_editing(callback_query: types.CallbackQuery, state: FSMContext):
    data = callback_query.data
    post_id = int(data.split('_')[-1])
    data = data.split('_')[:-1]
    action = "_".join(data)
    match action:
        case "change_planed_post_schedule":
            await callback_query.message.edit_text("Введіть час у форматі і виберіть дату: <b>00:00</b>", parse_mode = "html", reply_markup = get_calendar())
            await state.set_data({"post_id": post_id})
            await state.set_state(ContentPlan.DATE)
        case "remove_planed_post":
            await Posts.delete(post_id)
            await callback_query.answer('Пост видалено')
            await callback_query.message.answer('У цьому розділі ви можете переглядати та редагувати всі заплановані публікації у своїх проектах. Виберіть канал для перегляду контент-плану:', reply_markup = await get_plan_kb(datetime.datetime.now()))
            await callback_query.message.delete()

async def edit_post_date(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        post_id = data['post_id']
        date_time_regex = r'\d{2}:\d{2}'
        date_string = message.text
        date = data.get("date")
        
        if not date:
            return await message.answer("Ви не вибрали дату")
        
        if search(date_time_regex, date_string):
            time = datetime.datetime.strptime(date_string, "%H:%M").time()
            date = datetime.datetime.combine(date, time)
            if date <= datetime.datetime.now():
                return await message.answer(f"Недійсна дата.Спробуйте ще раз")  
            
            data["delay"] = date
            await Posts.update("id", post_id, delay = date)
            await message.answer('У цьому розділі ви можете переглядати та редагувати всі заплановані публікації у своїх проектах. Виберіть канал для перегляду контент-плану:', reply_markup = await get_plan_kb(date))
            await state.set_state(ContentPlan.CHOOSE_DAY)
        else:
            await message.answer("Невірний формат дати.Спробуйте ще раз")

def register_content_plan(dp: Dispatcher):
    dp.register_callback_query_handler(plan_post, lambda cb: cb.data == "plan_post", state = ContentPlan.CHOOSE_DAY)
    dp.register_callback_query_handler(set_day, lambda cb: cb.data in ('next_day', 'prev_day'), state = ContentPlan.CHOOSE_DAY)
    dp.register_callback_query_handler(set_calendar_state, lambda cd: cd.data == "full_calendar", state = ContentPlan.CHOOSE_DAY)
    dp.register_callback_query_handler(set_full_calendar_day, lambda cd: "calendar_day" in cd.data, state = ContentPlan.DATE)
    dp.register_callback_query_handler(set_full_calendar_month, lambda cb: cb.data in ("prev_month", "next_month"), state = ContentPlan.DATE)
    dp.register_callback_query_handler(edit_planed_post, lambda cd: "edit_planed_post" in cd.data, state = ContentPlan.CHOOSE_DAY)
    dp.register_callback_query_handler(handle_planed_post_editing, lambda cb: "change_planed_post_schedule" in cb.data or "remove_planed_post" in cb.data, state = ContentPlan.CHOOSE_DAY)
    dp.register_message_handler(edit_post_date, state = ContentPlan.DATE)
    dp.register_message_handler(choose_plan_post_time, state = ContentPlan.CHOOSE_DATE)
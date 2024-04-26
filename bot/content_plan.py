from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from db.account import Posts
from create_bot import get_channel
from datetime import timedelta
from states import ContentPlan
from posting import process_new_post, edit_post
from keyboards import *
from re import search
from utils import IsAdminFilter, IsChannel


async def plan_post(callback_query: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        data['date'] = (datetime.datetime.now() + timedelta(data['date_offset'])).date()
        message = callback_query.message
        await message.delete_reply_markup()
        await message.answer("Введіть час у форматі і виберіть дату: <b>00:00</b> або <b>00 00</b>", parse_mode = "html", reply_markup = get_calendar().add(back_to_edit.inline_keyboard[0][0]))
        await state.set_state(ContentPlan.CHOOSE_DATE)

async def choose_plan_post_time(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        date_string = message.text
        date = data["date"]
    
    if len(date_string) == 4:
        date_string = "0" + date_string 
        
    if search(r'\d{2}:\d{2}', date_string) or search(r'\d{2} \d{2}', date_string):
        if ':' in date_string:
            time = datetime.datetime.strptime(date_string, "%H:%M").time()
        else:
            time = datetime.datetime.strptime(date_string, "%H %M").time()
        date_time = datetime.datetime.combine(date, time)
        if date_time <= datetime.datetime.now():
            return await message.answer(f"Недійсна дата.Спробуйте ще раз")  
        await process_new_post(message, state, date_time)
    else:
        await message.answer("Невірний формат дати.Спробуйте ще раз")


async def choose_plan_post_time_by_button(callback_data: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        date_string = callback_data.data.split('_')[-1]
        date = datetime.datetime.strptime(date_string, "%Y-%m-%d %H:%M:%S")
        now = datetime.datetime.now()
        new_date = datetime.datetime(year=now.year, month=now.month, day=now.day,
                             hour=date.hour, minute=date.minute, second=date.second)
        if new_date <= now:
            return await callback_data.answer(f"Недійсна дата.Спробуйте іншу", show_alert = True)  
        await process_new_post(callback_data.message, state, new_date)


async def set_day(callback_query: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        date = callback_query.data.split(":")[1]
        data['date'] = datetime.datetime.strptime(date, "%Y-%m-%d").date()
        await callback_query.answer(f"Ви обрали {date}")


async def set_full_calendar_day(callback_query: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        date = callback_query.data.split(":")[1]
        date = datetime.datetime.strptime(date, "%Y-%m-%d")
        await state.update_data({"date": date})
        if data.get('post_id'):
            await callback_query.answer(f'Ви вибрали: {date.strftime("%Y-%m-%d")}')
        else:
            await callback_query.message.edit_reply_markup(await get_plan_kb(await Posts.get('channel_id', get_channel(), True), date))
            await state.set_state(ContentPlan.CHOOSE_DAY)

async def set_full_calendar_month(callback_query: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        index = data.get("calendar") if data.get("calendar") else 0
        add = index + 1 if callback_query.data == "next_month" else index - 1
        data["calendar"] = add
        await callback_query.message.edit_reply_markup(get_calendar(add))


async def content_plan_list(message: types.Message, state: FSMContext):
    await state.finish()
    date = datetime.datetime.now()
    await message.answer('У цьому розділі ви можете переглядати та редагувати всі заплановані публікації у своїх проектах. Виберіть канал для перегляду контент-плану:',
    reply_markup = await get_plan_kb(await Posts.get('channel_id', get_channel(), True), date))
    await state.set_data({'date_offset': 0})
    await state.set_state(ContentPlan.CHOOSE_DAY)

async def set_calendar_state(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.message.edit_reply_markup(await get_plan_kb(None, datetime.datetime.now(), True))
    await state.set_state(ContentPlan.DATE)

async def edit_planned_post(callback_query: types.CallbackQuery, state: FSMContext):
    post_id = int(callback_query.data.split('_')[-1])
    message = callback_query.message
    await edit_post(message, state, post_id = post_id)
    await message.delete()

async def handle_planed_post_editing(callback_query: types.CallbackQuery, state: FSMContext):
    data = callback_query.data
    post_id = int(data.split('_')[-1])
    data = data.split('_')[:-1]
    action = "_".join(data)
    match action:
        case "change_planned_post":
            message = callback_query.message
            await edit_post(message, state, post_id)
        case "change_planed_post_schedule":
            await callback_query.message.answer("Введіть час у форматі і виберіть дату: <b>00:00</b>", parse_mode = "html", reply_markup = get_calendar())
            await state.set_data({"post_id": post_id})
            await state.set_state(ContentPlan.DATE)
        case "remove_planned_post":
            await Posts.delete(post_id)
            await callback_query.answer('Пост видалено')
            await callback_query.message.answer('У цьому розділі ви можете переглядати та редагувати всі заплановані публікації у своїх проектах. Виберіть канал для перегляду контент-плану:', reply_markup = await get_plan_kb(await Posts.get('channel_id', get_channel(), True), datetime.datetime.now()))
            await callback_query.message.delete()

async def edit_post_date(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        post_id = data['post_id']
        date_time_regex = r'\d{2}:\d{2}'
        date_string = message.text
        date = data.get("date")
        
        if not date:
            return await message.answer("Ви не вибрали дату")

        if len(date_string) == 4:
            date_string = "0" + date_string 
        
        if search(date_time_regex, date_string):
            time = datetime.datetime.strptime(date_string, "%H:%M").time()
            date = datetime.datetime.combine(date, time)
            if date <= datetime.datetime.now():
                return await message.answer(f"Недійсна дата.Спробуйте ще раз")  
            
            data["delay"] = date
            await Posts.update("id", post_id, delay = date)
            await message.answer('У цьому розділі ви можете переглядати та редагувати всі заплановані публікації у своїх проектах. Виберіть канал для перегляду контент-плану:', reply_markup = await get_plan_kb(await Posts.get('channel_id', get_channel(), True), date))
            await state.set_state(ContentPlan.CHOOSE_DAY)
        else:
            await message.answer("Невірний формат дати.Спробуйте ще раз")

def register_content_plan(dp: Dispatcher):
    dp.register_message_handler(content_plan_list, lambda m: m.text == "Контент-план", IsAdminFilter(), IsChannel(), state = '*')
    dp.register_callback_query_handler(plan_post, lambda cb: cb.data == "plan_post", state = ContentPlan.CHOOSE_DAY)
    dp.register_callback_query_handler(set_day, lambda cd: "calendar_day" in cd.data, state = ContentPlan.CHOOSE_DATE)
    dp.register_callback_query_handler(set_calendar_state, lambda cd: cd.data == "full_calendar", state = ContentPlan.CHOOSE_DAY)
    dp.register_callback_query_handler(set_full_calendar_day, lambda cd: "calendar_day" in cd.data, state = ContentPlan.DATE)
    dp.register_callback_query_handler(set_full_calendar_month, lambda cb: cb.data in ("prev_month", "next_month"), state = ContentPlan.DATE)
    dp.register_callback_query_handler(edit_planned_post, lambda cd: "edit_planned_post" in cd.data, state = ContentPlan.CHOOSE_DAY)
    dp.register_callback_query_handler(handle_planed_post_editing, lambda cb: "change_planed_post_schedule" in cb.data or "remove_planned_post" in cb.data or "change_planned_post" in cb.data, state = ContentPlan.CHOOSE_DAY)
    dp.register_message_handler(edit_post_date, state = ContentPlan.DATE)
    dp.register_message_handler(choose_plan_post_time, state = ContentPlan.CHOOSE_DATE)
    dp.register_callback_query_handler(choose_plan_post_time_by_button, lambda cb: "set_time" in cb.data, state = ContentPlan.CHOOSE_DAY)
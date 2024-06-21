from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from db.account import Posts
from create_bot import get_channel
from states import ContentPlan
from posting import process_new_post, edit_post
from keyboards import *
from utils import parse_date
from utils import IsAdminFilter, IsChannel


async def plan_post(callback_query: types.CallbackQuery, state: FSMContext):
    message = callback_query.message
    await message.delete_reply_markup()
    await message.answer(
"""Введіть час у форматі або виберіть дату: 
<strong>
18 01
18 01 16
18:01 16 8
18 01 16.08
18 01 16.8
18 01 16 8 2020
18:01 16.8.2020
</strong>""", parse_mode = "html", reply_markup = get_calendar().add(back_to_edit.inline_keyboard[0][0]))
    await state.set_state(ContentPlan.CHOOSE_DATE)

async def choose_plan_post_time(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        date_str = message.text
        date = data.get("date")
        date = parse_date(date_str, date)
        if date:
            if date <= datetime.datetime.now():
                return await message.answer(f"Недійсна дата.Спробуйте ще раз")  
            await process_new_post(message, state, date)
        else:
            await message.answer(f"Невірний формат.Спробуйте ще раз")  


async def choose_plan_post_time_by_button(callback_data: types.CallbackQuery, state: FSMContext):
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
        kb = callback_query.message.reply_markup.inline_keyboard
        for row in kb:
            for button in row:
                if button.callback_data == callback_query.data:
                    button.text = button.text + ""

async def set_full_calendar_day(callback_query: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        date = callback_query.data.split(":")[1]
        date = datetime.datetime.strptime(date, "%Y-%m-%d")
        await state.update_data({"date": date})
        if data.get('post_id'):
            await callback_query.answer(f'Ви вибрали: {date.strftime("%Y-%m-%d")}')
        else:
            await callback_query.message.edit_reply_markup(await get_plan_kb(await Posts.get('channel_id', get_channel(callback_query.from_user.id), True), date))
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
    reply_markup = await get_plan_kb(await Posts.get('channel_id', get_channel(message.from_id), True), date))
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
            await callback_query.message.answer("Виберіть дату публікації поста або введіть її в форматі: <b>18:01\n18 01\n18:01 16 8\n18 01 16.8.2020\n18 01 16 8 2020</b>", parse_mode = "html", reply_markup = get_calendar())
            await state.set_data({"post_id": post_id})
            await state.set_state(ContentPlan.DATE)
        case "remove_planned_post":
            await Posts.delete(post_id)
            await callback_query.answer('Пост видалено')
            await callback_query.message.answer('У цьому розділі ви можете переглядати та редагувати всі заплановані публікації у своїх проектах. Виберіть канал для перегляду контент-плану:', reply_markup = await get_plan_kb(await Posts.get('channel_id', get_channel(callback_query.from_user.id), True), datetime.datetime.now()))
            await callback_query.message.delete()

async def edit_post_date(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        post_id = data['post_id']
        date_str = message.text
        date = data.get("date")
        
        date = parse_date(date_str, date)
        if date <= datetime.datetime.now():
            return await message.answer(f"Недійсна дата.Спробуйте ще раз")  
        
        data["delay"] = date
        await Posts.update("id", post_id, delay = date)
        await message.answer('У цьому розділі ви можете переглядати та редагувати всі заплановані публікації у своїх проектах. Виберіть канал для перегляду контент-плану:', reply_markup = await get_plan_kb(await Posts.get('channel_id', get_channel(message.from_id), True), date))
        await state.set_state(ContentPlan.CHOOSE_DAY)


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
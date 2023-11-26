from aiogram import types, Dispatcher
from states import BotAdds
from aiogram.dispatcher import FSMContext
from db.account import Users,  Adds
from keyboards import *
from create_bot import bot
import re
from utils import IsAdminFilter


async def ask_media(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.message.answer("Надішліть текст, фото/відео:", reply_markup = back_to_menu())
    await state.set_state(BotAdds.MEDIA)


async def skip_btn(message: types.Message, state: FSMContext):
    await check_adds(message, state)


async def ask_for_btn(message: types.Message, state: FSMContext):
    await state.update_data({'text': message.caption or message.text, 'media': message.photo[-1] if message.photo else message.video})
    await state.set_state(BotAdds.BTN)
    await message.reply("Введіть кнопку у форматі: \n<em>1. Кнопка - посилання</em>\n<em>2. Кнопка - посилання</em>\n<em>3. Кнопка - посилання</em>", reply_markup = skip_menu(), parse_mode = "html")


async def check_adds(message: types.Message, state: FSMContext):
    regex_pattern = r'([^\-]+) - ([^\n]+)'

    matches = re.findall(regex_pattern, message.text)
    kb = None
    if matches:
        kb = types.InlineKeyboardMarkup(row_width = 1)

        for name, link in matches:
            button = types.InlineKeyboardButton(text = name, url = link)
            kb.add(button)
    
    await state.update_data({'kb': kb})
    await message.answer("Введіть час у форматі і виберіть дату: <b>00:00</b>", parse_mode = "html", reply_markup = get_calendar().add(back_to_edit.inline_keyboard[0][0]))     
    
    await state.set_state(BotAdds.DATE)

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
                await send_adds_to_users(message, state)
                await state.set_state(BotAdds.CHECK)
            else:                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  
                await message.answer("Невірний формат дати.Спробуйте ще раз")
        except ValueError:
            await message.answer("Невірний формат дати.Спробуйте ще раз")


async def send_adds_to_users(message: types.Message, state: FSMContext):
    users = await Users.get('bot_id', bot.id, True)
    async with state.proxy() as data:
        text = data.get("text")
        media = data.get("media")
        url_buttons = data.get("kb")
        delay = data.get('delay')
        buttons = "".join([ "".join([b.text + " - " + b.url + ("\n" if b == btn[-1] else " | ") for b in btn]) if isinstance(btn, list) else btn.text + " - " + btn.url + "\n" for btn in url_buttons.inline_keyboard])
        
        await Adds(message.message_id,
            bot_id = bot.id,
            adds_text = text,
            delay = delay,
            buttons = buttons,
            media = media
        )()

        if users and not delay:
            counter = 0
            for user in users:
                try:
                    channel = user['id']
                    if media:
                        if isinstance(media, types.PhotoSize):
                            await bot.send_photo(channel, media.file_id, text, reply_markup = kb)
                        elif isinstance(media, types.Video):
                            await bot.send_video(channel, media.file_id, text, reply_markup = kb)
                    else:
                        await bot.send_message(channel, text, reply_markup = kb)
                    counter += 1
                except:
                    pass
            await message.answer(f"Розсилка відбулася успішно.Кількість надсилань: <b>{counter}</b>", reply_markup = main_menu(), parse_mode = "html")
        else:
            await message.answer(f"База даних бота пуста.Спробуйте пізніше", reply_markup = main_menu())
    await state.finish()

async def planned_menue(message: types.Message, state: FSMContext):
    adds = await Adds.get("bot_id", bot.id, True)
    date_format = "%Y-%m-%d %H:%M:%S"

    day = datetime.timedelta(days = 1)
    curr_day = datetime.datetime.now()
    prev_day = (curr_day - day).date()
    next_day = (curr_day + day).date()
    
    if adds:
        today = list(filter(lambda add: datetime.datetime.strptime(add.get('delay'), date_format).date() == prev_day, adds))
        yesterday = list(filter(lambda add: datetime.datetime.strptime(add.get('delay'), date_format).date() == prev_day, adds))
        tommorow = list(filter(lambda add: datetime.datetime.strptime(add.get('delay'), date_format).date() == next_day, adds))
        planned_menue_message = f"""
        📅 Події
        
        Вчора:
        {yesterday[0]['adds_text'] if today else 'пусто'}

        Сьогодні:
        {today[0]['adds_text'] if today else 'пусто'}

        Завтра:
        {tommorow[0]['adds_text'] if tommorow else 'пусто'}
        """
    else:
        planned_menue_message = f"""
        📅 Події
        
        Вчора:
        пусто

        Сьогодні:
        пусто

        Завтра:
        пусто
        """
    await message.answer(planned_menue_message, reply_markup = get_adds_kb())

def register_adds(dp: Dispatcher):
    dp.register_message_handler(planned_menue, lambda m: m.text == "Розсилка", IsAdminFilter(), state = "*")
    dp.register_callback_query_handler(ask_media, lambda cb: cb.data == "create_add", IsAdminFilter(), state = "*")
    dp.register_message_handler(skip_btn, lambda m: m.text == "Пропустити", state = BotAdds.BTN)
    dp.register_message_handler(ask_for_btn, state = BotAdds.MEDIA, content_types = types.ContentTypes.PHOTO | types.ContentTypes.VIDEO | types.ContentTypes.TEXT)
    dp.register_callback_query_handler(choose_date_handler, state = BotAdds.DATE)
    dp.register_message_handler(delay_adds_handler, state = BotAdds.DATE)
    dp.register_message_handler(check_adds, state = BotAdds.BTN, content_types = types.ContentTypes.TEXT)
    dp.register_message_handler(send_adds_to_users, lambda m: m.text == "Опублікувати", state = BotAdds.CHECK)
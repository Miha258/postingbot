import subprocess
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.dispatcher import FSMContext
from aiogram import executor
from bot.db.account import Bots, Paynaments, Channels, Users, Posts, Greetings, Adds, Admins
import logging
from os import kill


logging.basicConfig(level = logging.INFO)

class BotStates(StatesGroup):
    TYPE = State()
    TOKEN = State()
    DELETE = State()

def check_token(token):
    try:
        Bot(token = token)
        return True
    except Exception as e:
        print(f"Token is invalid. Error: {str(e)}")
        return False

bot = Bot(token = '6385303816:AAFUdMwXkVpnV9EjtQb_liLrQriB0U58T0g')
storage = MemoryStorage()
dp = Dispatcher(bot, storage = storage)
bot_types = ["Постинг", "Привітальний"]
main_kb = ReplyKeyboardMarkup(keyboard = [[KeyboardButton("Мої боти"), KeyboardButton("Створити бота")]], resize_keyboard = True)

@dp.message_handler(commands = ['start'], state = "*")
async def newbot_command_handler(message: types.Message, state: FSMContext):
    await state.finish()
    await message.reply("""
<strong><b>Створіть свого бота в 2 етапа:</b></strong>              

1.<b>Створення бази для бота в @BotFather:</b>
  ◉Запустіть @BotFather та відправте йому команду /newbot
  ◉Придумайте і надішліть будь-яке ім'я для бота (це ім'я буде видно всім зверху)
  ◉Придумайте і надішліть будь-яке посилання (лінк) для бота. Важливо, щоб лінк мав закінчення "bot" і не був зайнятий іншим користувачем.

2.<b>Надішліть сюди токен бота:</b>
   Токен - це довгий набір символів, який ви отримаєте, виконавши попередній крок.\nСкопіюйте цей набір символів або просто перешліть повідомлення з токеном від @BotFather прямо сюди.

<strong>💡Увага: не використовуйте цей токен для заупску інших ботів.</strong>

<strong>Потрібна допомога? Задайте питання: </strong>
    """, parse_mode = "html", reply_markup = main_kb) 


@dp.callback_query_handler(lambda cb: cb.data == 'back_to_menu', state = "*")
async def back_to_menu(callback_query: types.CallbackQuery, state: FSMContext):
    await state.finish()
    await callback_query.message.answer('Скористайтеся меню:')

@dp.message_handler(lambda m: m.text in ('Створити бота', '/newbot'), state = '*')
async def get_bots(message: types.Message, state: FSMContext):
    await state.set_state(BotStates.TYPE)
    kb = ReplyKeyboardMarkup([[KeyboardButton(type) for type in bot_types]], resize_keyboard = True)
    await message.answer(f'<b>Оберіть тип бота:</b>', parse_mode = "html", reply_markup = kb)
    

@dp.message_handler(lambda m: m.text in ('Мої боти', '/mybots'), state = '*')
async def get_bots(message: types.Message):
    bots = await Bots.get("user_id", message.from_id, True)
    if not bots:
        return await message.answer(f'<b>У вас немає ботів.Створіть його, нажавши кнопку "Створити бота"</b>', parse_mode = "html")
    
    bots_kb = InlineKeyboardMarkup(inline_keyboard = [[InlineKeyboardButton((await Bot(_bot["token"]).get_me()).mention, callback_data = f"edit_bot_{_bot['id']}")] for _bot in bots])
    await message.answer(f'<b>Список ваших ботів:</b>', reply_markup = bots_kb, parse_mode = "html")


@dp.message_handler(lambda m: m.text in bot_types, state = BotStates.TYPE)
async def set_type(message: types.Message, state: FSMContext):
    type = message.text

    if type == "Привітальний":
        await state.set_data({"type": "inviting"})
    elif type == "Постинг":
        await state.set_data({"type": "posting"})

    await state.set_state(BotStates.TOKEN) 
    await message.answer(f'<b>Введіть токен вашого бота:</b>', parse_mode = "html")


@dp.message_handler(state = BotStates.TOKEN)
async def process_newbot_token(message: types.Message, state: FSMContext):
    data = await state.get_data()
    type = data["type"]
    new_bot_token = message.text.strip()
    owner = message.from_id

    bots = await Bots.get("user_id", message.from_id, True)
    bots =  [_bot["token"] for _bot in await Bots.get("user_id", message.from_id, True)] if bots else []

    if not check_token(new_bot_token):
        return await message.reply('Невірний токен.Спробуйте ще раз:') 
    
    elif message.text in bots:
        return await message.reply('Такий токен вже зарєстровано.Спробуйте інший') 

    process = subprocess.Popen(['python3', 'bot/main.py', new_bot_token, str(owner), type])
    bot = Bot(token = new_bot_token)
    bot = await bot.get_me()
    await message.reply(f'{bot.mention} запущений.Використвуйте /start для початку роботи.Викорисутовуйте /bots, щоб відкрити список ботів', reply_markup = main_kb)
    await Bots(bot.id, user_id = message.from_id, token = message.text, type = type, username = '@' + bot.username, p_id = process.pid)()
    await state.finish()  


@dp.callback_query_handler(lambda cb: "edit_bot" in cb.data)
async def edit_bot(callback_query: types.CallbackQuery):
    bot_id = callback_query.data.split('_')[-1]
    _bot = await Bots.get('id', bot_id)
    edit_kb = InlineKeyboardMarkup(inline_keyboard = [
        [InlineKeyboardButton('Видалити', callback_data = f'delete_bot_{bot_id}')],
        [InlineKeyboardButton('Повернутися в меню', callback_data = 'back_to_menu')]
    ])
    await callback_query.message.edit_text(f'Виберть дію для {_bot["username"]}:', reply_markup = edit_kb)


@dp.callback_query_handler(lambda cb: "delete_bot" in cb.data)
async def delete_bot(callback_query: types.CallbackQuery):
    bot_id = callback_query.data.split('_')[-1]
    bot = await Bots.get("id", bot_id)
    kill(bot['p_id'], 9)

    await Bots.delete(bot_id)
    channels = await Channels.get("bot_id", bot_id, True)
    if channels:
        for channel in channels:
            await Channels.delete(channel['id'])

    posts = await Posts.get("bot_id", bot_id, True)
    if posts:
        for post in posts:
            await Posts.delete(post['id'])

    greetings = await Greetings.get("bot_id", bot.id, True)
    if greetings:
        for greet in greetings:
            await Greetings.delete(greet['id'])

    users = await Users.get('bot_id', bot.id, True)
    if users:
        for user in users:
            await Users.delete(user['id'])
    
    bot = await Bot(token = bot['token']).get_me()
    await callback_query.message.answer(f'{bot.mention} був успішно видалений')
    await callback_query.message.delete()

async def start_bots(_):
    await Bots.init_table({
        "id": "INT",
        "user_id": "INT",
        "p_id": "INT",
        "token": "TEXT",
        "username": "TEXT",
        "type": "TEXT",
        "subscription": "BOOLEAN",
        "subscription_to": "DATE"
    })

    await Channels.init_table({
        "id": "INT",
        "chat_id": "INT",
        "bot_id": "INT",
        "name": "TEXT",
        "subscribers": "INT",
        "watermark": "TEXT",
        "capcha": "TEXT"
    })

    await Paynaments.init_table({
        "id": "INT",
        "user_id": "INT",
        "amount": "INT",
        "currency": "TEXT",
        "created_at": "DATETIME",
        "paid_at": "DATETIME"
    })

    await Users.init_table({
        "id": "INT",
        "bot_id": "INT"
    })
    
    await Greetings.init_table({
        "id": "INT",
        "bot_id": "INT",
        "channel_id": "TEXT",
        "greet_text": "TEXT",
        "autodelete": "INT",
        "delay": "INT",
        "buttons": "TEXT",
        "image": "TEXT"
    })

    await Posts.init_table({
        "id": "INT",
        "bot_id": "INT",
        "channel_id": "TEXT", 
        "post_text": "TEXT",
        "hidden_extension_text_1": "TEXT",
        "hidden_extension_text_2": "TEXT",
        "hidden_extension_btn": "TEXT",
        "url_buttons": "TEXT",
        "parse_mode": "TEXT",
        "comments": "BOOLEAN",
        "notify": "BOOLEAN",
        "watermark": "TEXT",
        "delay": "DATE",
        "media": "TEXT",
        "autodelete": "DATE",
        "is_published": "BOOLEAN",
        "preview": "BOOLEAN"
    })
    
    await Adds.init_table({
        "id": "INT",
        "bot_id": "INT",
        "adds_text": "TEXT",
        "delay": "DATE",
        "buttons": "TEXT",
        "media": "TEXT",
        "is_published": "BOOLEAN"
    })

    await Admins.init_table({
        "id": "INT",
        "username": "TEXT",
        "bot_id": "INT",
        "channels": "TEXT"
    })
    
    user_bots = await Bots.all()
    if user_bots:
        for _bot in user_bots:
            try:
                token = _bot["token"]
                owner = _bot["user_id"]
                type = _bot["type"]
                process = subprocess.Popen(['python3', 'bot/main.py', token, str(owner), type])
                await Bots.update('id', _bot['id'], p_id = process.pid)
                
                bot_instance = Bot(token = token)
                bot_mention = await bot_instance.get_me()

                await bot.send_message(owner, f'Ваш <a href="https://t.me/{bot_mention.mention}">бот</a> знову працює!', parse_mode = types.ParseMode.HTML)
            except Exception as e:
                await bot.send_message(owner, "Виникла помилка при запуску вашого бота.Зверніться в підтримку")  


async def stop_bots(_): 
    user_bots = await Bots.all()
    if user_bots:
        for _bot in user_bots:
            token = _bot["token"]
            owner = _bot["user_id"]
            
            bot_instance = Bot(token = token)
            bot_mention = await bot_instance.get_me()
            await bot.send_message(owner, f'Ваш {bot_mention.mention} тимчасово припиняє роботу.', reply_markup = InlineKeyboardMarkup([[
                InlineKeyboardButton("Звязатися з нами", url = "https://t.me/")
            ]]))


if __name__ == '__main__':
    executor.start_polling(dp, on_startup = start_bots, on_shutdown = stop_bots)
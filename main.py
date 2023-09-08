import subprocess
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.dispatcher import FSMContext
from aiogram import executor
from bot.db.account import Bots, Paynaments, Channels, Users
import logging

logging.basicConfig(level = logging.INFO)

class BotStates(StatesGroup):
    TYPE = State()
    TOKEN = State()

def check_token(token):
    try:
        Bot(token = token)
        return True
    except Exception as e:
        print(f"Token is invalid. Error: {str(e)}")
        return False

bot = Bot(token = '6374236249:AAGV_LhSYGnWbJA4wEYIyt0-ZiwAZUj_k5s')
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


@dp.message_handler(text = "Створити бота")
async def get_bots(message: types.Message, state: FSMContext):
    await state.set_state(BotStates.TYPE)
    
    kb = ReplyKeyboardMarkup([[KeyboardButton(type) for type in bot_types]], resize_keyboard = True)
    await message.answer(f'<b>Оберіть тип бота:</b>', parse_mode = "html", reply_markup = kb)
    

@dp.message_handler(text = "Мої боти", state = "*")
async def get_bots(message: types.Message):
    bots = await Bots.get("user_id", message.from_id, True)
    if not bots:
        return await message.answer(f'<b>У вас немає ботів.Стовріть його, нажавши кнопку "Створити бота"</b>', parse_mode = "html")
    
    bots = '\n'.join([(await Bot(_bot["token"]).get_me()).mention for _bot in bots])
    await message.answer(f'<b>Список ваших ботів: \n\n{bots}</b>', parse_mode = "html")


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
        return await message.reply('Невірний токен.Спробуйие ще раз:') 
    
    elif message.text in bots:
        return await message.reply('Такий токен вже зарєстровано.Спробуйте інший') 

    subprocess.Popen(['python3', 'bot/main.py', new_bot_token, str(owner), type])

    bot = Bot(token = new_bot_token)
    bot = await bot.get_me()
    await message.reply(f'{bot.mention} запущений.Використвуйте /start для почтку роботи.Викорисутовуйте /bots, щоб відкрити список ботів', reply_markup = main_kb)
    await Bots(bot.id, user_id = message.from_id, token = message.text, type = type)()
    await state.finish()  


async def start_bots(_):
    await Bots.init_table({
        "id": "INT",
        "user_id": "INT",
        "token": "TEXT",
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
    
    user_bots = await Bots.all()
    if user_bots:
        for _bot in user_bots:
            try:
                token = _bot["token"]
                owner = _bot["user_id"]
                type = _bot["type"]
                subprocess.Popen(['python3', 'bot/main.py', token, str(owner), type])

                bot_instance = Bot(token = token)
                bot_mention = await bot_instance.get_me()

                await bot.send_message(owner, f'Ваш <a href="https://t.me/{bot_mention.mention}">бот</a> знову працює!', parse_mode="html")
            except Exception as e:
                await bot.send_message(owner, "Виникла помилка при запуску вашого бота")  


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
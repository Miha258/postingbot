from create_bot import bot, storage, bot_type
from aiogram import Dispatcher, types
from aiogram.utils.callback_data import CallbackData
from aiogram import executor
from keyboards import *
import logging
from request import register_request
from greet import register_greet
from posting import register_posting
from adds import register_adds
from channels import register_channels, IsAdminFilter
from aiogram.dispatcher import FSMContext
from paynaments import register_paynaments
from db.account import *

logging.basicConfig(level = logging.INFO)
dp = Dispatcher(bot, storage = storage) 

@dp.message_handler(IsAdminFilter(), commands = ['start'], state = "*")   
async def start_command(message: types.Message, state: FSMContext):
    await state.finish()
    await message.reply(""" 
    Цей бот призначений особисто для вас і призначений для планування відкладених публікацій. Використовуйте його для створення привабливих записів у вашому каналі або чаті.
Для початку роботи скористайтесь меню або командами.
/help — надасть вам довідку та корисні посилання.
        """, reply_markup = main_menu())


@dp.callback_query_handler(CallbackData("back_to_menu").filter(), state = "*")
async def back_to_menu(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.message.delete()
    await callback_query.message.answer("Використовуйте кнопки нижче:", reply_markup = main_menu())
    await state.finish()


@dp.message_handler(lambda m: m.text == "Повернутися в меню", state = "*")
async def back_to_menu(message: types.Message, state: FSMContext):
    await message.answer("Використовуйте кнопки нижче:", reply_markup = main_menu())
    await state.finish()


if __name__ == '__main__':
    if bot_type == "inviting":
        register_request(dp)
        register_greet(dp)
        register_adds(dp)
    elif bot_type == "posting": 
        register_posting(dp)
        
    register_paynaments(dp)
    register_channels(dp)
    executor.start_polling(dp, skip_updates = True)
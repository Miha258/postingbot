from aiogram import types, Dispatcher
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from states import *
from utils import *
from db.account import Paynaments, Bots
import aiohttp
from datetime import datetime, timedelta
from keyboards import *

tarifs = {
    6.99: "1 місяць 6.99$.",
    8.99: "3 місяця 8.99$.",
    12.99: "6 місяців 12.99$.",
    18.99: "1 рік 18.99$."
}

headers = {
    'Host': 'pay.crypt.bot',
    'Crypto-Pay-API-Token': "109873:AAkLNPN7OUcdIfGIXWP4lpznafNepPl45p8"
}


choice_tarif = InlineKeyboardMarkup(inline_keyboard = [[InlineKeyboardButton(name, callback_data = f"price_{price}")] for price, name in list(tarifs.items())])
choice_tarif.add(back_btn)

async def choose_tarif(message: types.Message):
    bot = await Bots.get("id", message.bot.id)
    if bot:
        if bot["subscription"]:
            await message.answer(f"Ви вже оформили тариф до <b>{bot['subscription_to'].split(' ')[0]}</b>", parse_mode = "html")
        else:
            await message.answer("Виберіть тариф", reply_markup = choice_tarif)

async def create_invoice(callback_query: types.CallbackQuery):
    price = callback_query.data.split("_")[1]
    async with aiohttp.ClientSession(headers = headers) as session:
        async with session.get(f'https://pay.crypt.bot/api/createInvoice?asset=USDT&amount={price}3&allow_anonymous=False') as response:
            response = await response.json()
            check = response["result"]
            url = check.get("pay_url")
            check_id = check.get('invoice_id')

            reply_markup = InlineKeyboardMarkup(inline_keyboard = [
                [InlineKeyboardButton(f"Оплатити {tarifs[float(price)]}", url)],
                [InlineKeyboardButton("Перевірити", callback_data = f"check_invoice_{price}_{check_id}")]
            ])
            reply_markup.add(back_btn)
            await callback_query.message.answer("Чек успішно створено.Після оплати нажміть <b>\"Перевірити\"</b>", reply_markup = reply_markup, parse_mode = "html")

async def check_invoice(callback_query: types.CallbackQuery):
    message = callback_query.message
    check_id = callback_query.data.split('_')[-1]
    tarif = tarifs[float(callback_query.data.split('_')[-2])]
    
    async with aiohttp.ClientSession(headers = headers) as session:
        async with session.get(f'https://pay.crypt.bot/api/getInvoices?invoice_id={check_id}') as response:
            response = await response.json()
            paynament = response['result']['items'][0]
  
            if paynament['status'] != 'paid':
                await message.delete_reply_markup()

                invoice_id = paynament.get('invoice_id')
                amount = paynament.get('amount')
                currency = paynament.get('asset')
                created_at = paynament.get('created_at')
                paid_at = paynament.get('paid_at')

                await Paynaments(invoice_id, user_id = callback_query.from_user.id, amount = amount, currency = currency, created_at = created_at, paid_at = paid_at)()
                await Bots.update("id", callback_query.message.from_id, subscription = True, subscription_to = datetime.now() + timedelta(days = 31 * int(tarif[0])))
                await message.edit_text(f"Оплату <b>підтверджено</b>.Вітаю з придбанням тарифу: <b>{tarif}</b>", parse_mode = "html")
            else:
                await callback_query.answer("Оплату не підтверджено.Спробуйте ще раз або зверніться в підтримку", show_alert = True)
   
def register_paynaments(dp: Dispatcher):
    dp.register_message_handler(choose_tarif, lambda m: m.text == 'Тарифи')
    dp.register_callback_query_handler(create_invoice, lambda a: "price_" in a.data)
    dp.register_callback_query_handler(check_invoice, lambda a: "check_invoice" in a.data)
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton
from create_bot import bot_type

back_btn = InlineKeyboardButton('Повернутися в меню', callback_data = "back_to_menu")

def main_menu():
    buttons = [KeyboardButton('Розсилка')]
    
    if bot_type == "inviting":
        buttons.append(KeyboardButton('Привітання'))
        buttons.append(KeyboardButton('Керування заявками'))
    elif bot_type == "posting":
        buttons.append(KeyboardButton('Постинг'))

    
    markup = ReplyKeyboardMarkup(resize_keyboard = True, keyboard = [
        buttons,
        [KeyboardButton("Тарифи")]
    ])
    return markup

def back_to_menu():
    keyboard = ReplyKeyboardMarkup(resize_keyboard = True)
    keyboard.add(back_btn)
    return keyboard

def skip_menu():
    keyboard = ReplyKeyboardMarkup(resize_keyboard = True)
    keyboard.add(KeyboardButton("Пропустити"))
    keyboard.add(KeyboardButton('Повернутися в меню'))
    return keyboard

def check_add_menu():
    keyboard = ReplyKeyboardMarkup(resize_keyboard = True)
    keyboard.add(KeyboardButton('Опублікувати'))
    keyboard.add(KeyboardButton('Редагувати'))
    keyboard.add(KeyboardButton('Повернутися в меню'))
    return keyboard
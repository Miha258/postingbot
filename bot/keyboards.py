from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from create_bot import bot_type
import datetime, calendar

back_btn = InlineKeyboardButton('Повернутися в меню', callback_data = "back_to_menu")
back_to_edit = InlineKeyboardMarkup(inline_keyboard = [
    [InlineKeyboardButton('Повернутися до редагування', callback_data = "back_to_edit")]
])
make_new_post_kb = InlineKeyboardMarkup(inline_keyboard = [
    [InlineKeyboardButton('Створити ще один пост', callback_data = 'create_post_again')]
])
confirm_post_kb = InlineKeyboardMarkup(inline_keyboard = [
    [InlineKeyboardButton('Скасувати', callback_data = 'cancle_post')],
    [InlineKeyboardButton('Підтвердити', callback_data = 'create_post')]
])

def main_menu():
    buttons = []
    
    if bot_type == "inviting":
        buttons.append(KeyboardButton('Привітання'))
        buttons.append(KeyboardButton('Керування заявками'))
        buttons.append(KeyboardButton('Розсилка'))
    elif bot_type == "posting":
        buttons.append(KeyboardButton('Постинг'))
        buttons.append(KeyboardButton('Контент-план'))
        buttons.append(KeyboardButton('Редагувати пост'))

    
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

def get_user_kb(data: dict):
    user_kb = InlineKeyboardMarkup()

    if data.get("hidden_extension_btn"):
        user_kb.add(InlineKeyboardButton(data["hidden_extension_btn"], callback_data = "hidden_extension_use"))

    url_buttons = data.get("url_buttons")
    if url_buttons:
        if isinstance(url_buttons, list):
            user_kb.add(*data["url_buttons"])
        elif isinstance(url_buttons, str):
            buttons = [InlineKeyboardButton(btn.split(' - ')[0], btn.split(' - ')[1]) for btn in url_buttons.split('\n') if btn]
            print(buttons)
            user_kb.add(*buttons)

    user_kb = user_kb if user_kb.inline_keyboard else None
    return user_kb


def get_calendar(month: int = 0):
    inline_markup = InlineKeyboardMarkup(row_width=7)
    date = datetime.datetime.today()

    if month < 0:
        date = date.replace(year = date.year + 1) 
    
    start = 1 if month else date.day
    end = calendar.monthrange(date.year, date.month + month)[1]
    for day in range(start, end + 1):
        inline_markup.insert(InlineKeyboardButton(str(day), callback_data = f"calendar_day:{date.year}-{date.month + month}-{day}"))
    
    months = [
        "Січень", "Лютий", "Березень", "Квітень", "Травень", "Червень",
        "Липень", "Серпень", "Вересень", "Жовтень", "Листопад", "Грудень"
    ]   

    inline_markup.row(
        InlineKeyboardButton("Назад", callback_data = "prev_month"),
        InlineKeyboardButton(months[date.month + month - 1], callback_data = "current_month"),
        InlineKeyboardButton("Вперед", callback_data = "next_month"),
    )
    return inline_markup

def get_edit_planed_post_kb(post_id: int):
    kb = InlineKeyboardMarkup(inline_keyboard = [
        [InlineKeyboardButton('Перенести', callback_data = f'change_planed_post_schedule_{post_id}')],
        [InlineKeyboardButton('Видалити', callback_data = f'remove_planed_post_{post_id}')]
    ])
    return kb
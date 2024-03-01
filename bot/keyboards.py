from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from create_bot import bot_type, bot
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

confirm_deley_post_kb = InlineKeyboardMarkup(inline_keyboard = [
    back_to_edit.inline_keyboard[0],
    [InlineKeyboardButton('Відкласти пост', callback_data = 'delay_post')]
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
        [KeyboardButton("Вибрати канал")],
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

def edit_capcha_kb(status = False, capcha_buttons: str = None):
    inline_markup = InlineKeyboardMarkup(inline_keyboard = [
        [InlineKeyboardButton('Редагувати', callback_data = 'edit_capcha')],
        [InlineKeyboardButton('Вимкнути', callback_data = 'set_capcha_status')] if status else [InlineKeyboardButton('Увімкнути', callback_data = 'set_capcha_status')],
        [InlineKeyboardButton('Повернутися в меню', callback_data = 'back_to_greet_menu')]
    ])

    if capcha_buttons:
        capcha_data = capcha_buttons.split(' , ')
        capcha_answers = {}
        btns = []
        for data in capcha_data:
            reply, answer = data.split(' | ')
            capcha_answers[reply] = answer
            btns.append(InlineKeyboardButton(reply, callback_data = '_'))
        inline_markup.inline_keyboard.insert(0, btns)

    return inline_markup

def get_user_kb(data: dict):
    user_kb = InlineKeyboardMarkup()
    
    if data.get("hidden_extension_btn"):
        user_kb.add(InlineKeyboardButton(data["hidden_extension_btn"], callback_data = "hidden_extension_use"))
    
    url_buttons = data.get("url_buttons")
    if url_buttons:
        if isinstance(url_buttons, list):
            row_btns = []
            column_buttons = 0
            for btn in url_buttons:
                if isinstance(btn, list):
                    user_kb.inline_keyboard.insert(column_buttons, btn)
                    column_buttons += 1
                elif isinstance(btn, InlineKeyboardButton):
                    row_btns.append(btn)

        elif isinstance(url_buttons, str):
            row_btns = 0
            for i, btn in enumerate(url_buttons.split('\n')):
                if btn:
                    if '|' not in btn:
                        name, url = btn.split(' - ')
                        user_kb.inline_keyboard.insert(i + 1, [InlineKeyboardButton(name, url)])
                    elif '|' in btn:
                        btns = []
                        for b in btn.split('|'):
                            name, url = b.split(' - ')
                            btns.append(InlineKeyboardButton(name, url))
                        user_kb.inline_keyboard.insert(row_btns, btns)
    
        if row_btns:
            user_kb.inline_keyboard.insert(0, row_btns)
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
        [InlineKeyboardButton('Редагувати', callback_data = f'change_planned_post_{post_id}')],
        [InlineKeyboardButton('Перенести', callback_data = f'change_planed_post_schedule_{post_id}')],
        [InlineKeyboardButton('Видалити', callback_data = f'remove_planned_post_{post_id}')]
    ])
    return kb

def get_adds_kb():
    kb = InlineKeyboardMarkup(inline_keyboard = [
        [   
            InlineKeyboardButton('Розсилка', callback_data = f'create_add'),
            InlineKeyboardButton('← Розклад', callback_data = f'adds_calendar')
        ]
    ])
    return kb

def get_autodelete_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup()
    button_rows = [
        [24],
        [36],
        [48],
        [72]
    ]
    buttons = []
    for row in button_rows:
        button_row = []
        for button in row:
            button_row.append(InlineKeyboardButton(f'{button}h', callback_data = f'set_autodelete_{button}'))
        buttons.append(button_row)
    kb.inline_keyboard = buttons
    return kb

async def get_plan_kb(data, date: datetime.datetime, full = False):
    kb = InlineKeyboardMarkup()
    if data:
        for record in data:
            if record['delay'] and not record['is_published']:
                delay = datetime.datetime.strptime(record['delay'], "%Y-%m-%d %H:%M:%S")
                if delay.date() == date.date():
                    kb.add(InlineKeyboardButton(
                        f"📅 {record['post_text'][:15]}... {':'.join(record['delay'].split(' ')[1].split(':')[:-1])}",
                        callback_data = f'edit_planned_post_{record["id"]}'
                    )
            )
    if full:
        return get_calendar()  
        
    date_fromat = "%Y-%m-%d"
    plus_day = datetime.timedelta(days = 1)

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

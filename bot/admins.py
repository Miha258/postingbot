from db.account import Admins
from aiogram.dispatcher import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram import types, Dispatcher
from create_bot import bot, owner
from states import AdminsStates
from utils import IsOwnerFilter


admins_actions_kb = InlineKeyboardMarkup(inline_keyboard = [[
    InlineKeyboardButton('Додати ➕', callback_data = "add_admin"),
    InlineKeyboardButton('Прибрати ➖', callback_data = "remove_admin")
]])

async def admins_list(message: types.Message):
    admins = await Admins.get('bot_id', bot.id, True)
    if admins:
        print(admins)
        admins = "\n".join([f"{i}. @" + admin["username"] for i, admin in enumerate(admins, 1)])
        await message.answer("Список адмінів:\n" + admins, reply_markup = admins_actions_kb)
    else:
        await message.answer("Список одмінів пустий, тут ви зможете передати доступ до бота:\n", reply_markup = admins_actions_kb)

async def admins_handler(callback_data: types.CallbackQuery, state: FSMContext):
    message = callback_data.message
    action = callback_data.data
    
    match action:
        case "add_admin":
            await message.answer("Перешліть повідомлення користувача, якого бажаєте зробити адміном")
            await state.set_state(AdminsStates.ADD_ADMIN)
        case "remove_admin":
            await message.answer("Введіть юзернейм адміна, якого бажаєте видалити:")
            await state.set_state(AdminsStates.REMOVE_ADMIN)


async def add_admin(message: types.Message, state: FSMContext):
    target = message.forward_from
    if target:
        admin = await Admins.get('id', message.from_id)
        if admin:
            return await message.answer('Адмін вже є у списку, оберіть іншого')

        if target.id == int(owner):
            return await message.answer('Ви не можете додати себе, як адміна, спробуйте когось іншого')
        
        await Admins(target.id, bot_id = bot.id, username = target.username)()
        await state.finish()
        await admins_list(message)
    else:
        await message.answer('Спробуйте переслати повідомлення від користувача:')


async def remove_admin(message: types.Message, state: FSMContext):
    username = message.text.replace('@', '')
    admin = await Admins.get('username', username)
    if admin:
        if admin["bot_id"] != bot.id:
            return await message.answer('Цей користувач не є адміном цього бота')
        
        await Admins.delete(admin['id'])
        await state.finish()
        await admins_list(message)
    else:
        await message.answer('Користувач не зараєстрований як адміном цього бота')


def register_admins(dp: Dispatcher):
    dp.register_message_handler(admins_list, lambda m: m.text == "Назначити адміна", IsOwnerFilter())
    dp.register_callback_query_handler(admins_handler, lambda cb: cb.data in ("remove_admin", "add_admin"))
    dp.register_message_handler(add_admin, state = AdminsStates.ADD_ADMIN)
    dp.register_message_handler(remove_admin, state = AdminsStates.REMOVE_ADMIN)
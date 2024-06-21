from db.account import Admins, Channels
from aiogram.dispatcher import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram import types, Dispatcher
from create_bot import bot, owner, set_channel
from states import AdminsStates
from utils import IsOwnerFilter


def admins_actions_kb(admins):
    kb = InlineKeyboardMarkup()
    if admins:
        for admin in admins:
            kb.add(InlineKeyboardButton(admin['username'], callback_data = f"edit_admin_{admin['id']}"))
    
    kb.add(InlineKeyboardButton('Додати ➕', callback_data = "add_admin"))
    kb.add(InlineKeyboardButton('Прибрати ➖', callback_data = "remove_admin"))
    return kb


async def get_permissions_kb(user_id):
    kb = types.InlineKeyboardMarkup()
    bot_channels = await Channels.get('bot_id', bot.id, True)
    channels = await Admins.get("id", user_id)
    if channels:
        if not channels.data.get("channels"):
            channels = []
        else:
            channels = channels["channels"].split(",")
        if bot_channels:
            for channel in bot_channels:
                channel_name = channel['name'] + " ❌" if str(channel['chat_id']) not in channels else channel['name'] + " ✅"
                callback_data = f"remove_channel_{user_id}_{channel['chat_id']}" if str(channel['chat_id']) in channels else f"set_channel_{user_id}_{channel['chat_id']}"
                try:
                    kb.add(types.InlineKeyboardButton(channel_name, callback_data = callback_data))
                except:
                    pass
            kb.add(types.InlineKeyboardButton('Назад', callback_data = 'back_to_admins_list'))
            return kb
        

async def back_to_admins_list(callback_data: types.CallbackQuery, state: FSMContext):
    await state.finish()
    text, kb = await admins_list(callback_data.message, state, True)
    await callback_data.message.edit_text(text, reply_markup = kb)

async def admins_list(message: types.Message, state: FSMContext, _return = False):
    await state.finish()
    admins = await Admins.get('bot_id', bot.id, True)
    text = ""

    if admins:
        text = "Список адмінів, тут ви можете додавати, видаляти або редагуати адміністраторів:"
    else:
        text = "Список адмінів пустий, тут ви зможете передати доступ до бота:\n"
    
    kb = admins_actions_kb(admins)
    if _return:
        return text, kb

    await message.answer(text, reply_markup = kb)


async def admins_handler(callback_data: types.CallbackQuery, state: FSMContext):
    message = callback_data.message
    action = callback_data.data
    if 'edit_admin' in action:
        admin_id = action.split('_')[-1]
        await state.set_state(AdminsStates.EDIT_ADMIN)
        return await message.edit_text('Виберіть канали для редагування:', reply_markup = await get_permissions_kb(admin_id))

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


async def edit_admin_permissions(callback_data: types.CallbackQuery):
    action = callback_data.data.split('_')[0]
    channel = callback_data.data.split('_')[-1]
    admin_id = callback_data.data.split('_')[-2]
    channels = await Admins.get('id', admin_id)
    if channels:
        if not channels.data.get("channels"):
            channels = []
        else:
            channels = channels["channels"].split(",")
    else:
        channels = []

    match action:
        case 'set':
            channels.append(channel)
        case 'remove':
            set_channel(int(admin_id), "")
            channels.remove(channel)
    await Admins.update('id', admin_id, channels = ','.join(channels))
    await callback_data.message.edit_reply_markup(reply_markup = await get_permissions_kb(admin_id))

def register_admins(dp: Dispatcher):
    dp.register_message_handler(admins_list, lambda m: m.text == "Назначити адміна", IsOwnerFilter(), state = "*")
    dp.register_callback_query_handler(admins_handler, lambda cb: cb.data in ("remove_admin", "add_admin") or 'edit_admin' in cb.data)
    dp.register_message_handler(add_admin, state = AdminsStates.ADD_ADMIN)
    dp.register_message_handler(remove_admin, state = AdminsStates.REMOVE_ADMIN)
    dp.register_callback_query_handler(back_to_admins_list, lambda cb: cb.data == 'back_to_admins_list', state = AdminsStates.EDIT_ADMIN)
    dp.register_callback_query_handler(edit_admin_permissions, state = AdminsStates.EDIT_ADMIN)
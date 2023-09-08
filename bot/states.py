from aiogram.dispatcher.filters.state import State, StatesGroup


class BotStates(StatesGroup):
    ADDING_POST = State()
    EDITING_POST = State()
    ADDING_CHANNEL = State()
    BOT_CHECKING = State()
    CHAT_GPT = State()
    SET_GREED_TEXT = State()
    SET_CHANNEL = State()
    CHOOSE_CHANNEL = State()
    AMOUNT = State()
    TIMEOUT = State()

class BotAdds(StatesGroup):
    MEDIA = State()
    BTN = State()
    TEXT = State()
    CHECK = State()

class EditStates(StatesGroup):
    EDITING_TEXT = State()
    ATTACHING_MEDIA = State()
    EDITING_FORMAT = State()
    HIDDEN_EXTENSION_BTN = State()
    HIDDEN_EXTENSION_TEXT_1 = State()
    HIDDEN_EXTENSION_TEXT_2 = State()
    DISABLE_COMMENTS = State()
    DISABLE_REPOST = State()
    PARSE_MODE = State()
    URL_BUTTONS = State()
    TIME = State()
    DATE = State()


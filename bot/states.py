from aiogram.dispatcher.filters.state import State, StatesGroup


class BotStates(StatesGroup):
    ADDING_POST = State()
    EDITING_POST = State()
    EDITING_CAPCHA = State()
    ADDING_CHANNEL = State()
    BOT_CHECKING = State()
    CHAT_GPT = State()
    SET_CHANNEL = State()
    CHOOSE_CHANNEL = State()
    AMOUNT = State()
    TIMEOUT = State()
    CHANGE_POST = State()

class BotAdds(StatesGroup):
    TEXT = State()
    MEDIA = State()
    BTN = State()
    DATE = State()
    CHECK = State()


class ContentPlan(StatesGroup):
    CHOOSE_DAY = State()
    CHOOSE_DATE = State()
    EDIT_POST = State()
    DATE = State()


class EditStates(StatesGroup):
    EDITING_TEXT = State()
    AUTODELETE = State()
    WATERMARK_TEXT = State()
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
    COMFIRM = State()

class CustomGreetSatates(StatesGroup):
    MEDIA = State()
    BUTTONS = State()
    EDIT_BUTTONS = State()
    EDIT_DELAY = State()
    EDIT_AUTODELETE = State()
    EDIT_TEXT = State()
    EDIT_MEDIA = State()
    GREET_EDITING = State()
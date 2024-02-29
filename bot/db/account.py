from .main import DB
import asyncio
from datetime import datetime

loop = asyncio.get_event_loop()
posting = loop.run_until_complete(DB("posting.db")())

class Table:
    def __str__(self) -> str:
        return f"<{self.__class__.__name__}Data {self.data}>"

    def __init__(self, id: int, **kwargs) -> None:
        kwargs["id"] = id
        self.id = id
        self.data = kwargs

    async def __call__(self):
        await posting.create_record(self.table, self.data) 
    
    def __getitem__(self, key):
        return self.data[key]
    
    def to_dict(self):
        return self.data

    @classmethod
    async def init_table(cls, table_data: dict):
        await posting.create_table(cls.table, table_data)
    
    @classmethod
    async def get(cls, by: str, value, all: bool = False):
        data = await posting.read_record(cls.table, by, value, all)
        if all:
            return [Table(**record) for record in data ] if data else None
        return Table(**data) if data else None
    
    @classmethod
    async def all(cls):
        records = await posting.get_all_records(cls.table)
        return [Table(**record) for record in records] if records else None

    @classmethod
    async def update(cls, by: int, value, **kwargs):
        await posting.update_record(cls.table, by, value, kwargs)
        return await cls.get(by, value)
    
    @classmethod
    async def delete(cls, id):
        await posting.delete_record(cls.table, id)



class Bots(Table):
    table = "bots"
    
class Paynaments(Table):
    table = "paynaments"

class Channels(Table):
    table = "channels"

class Users(Table):
    table = "users"

class Adds(Table):
    table = "adds"

    @classmethod
    async def save_add(
        cls,
        id: int, 
        bot_id: int, 
        adds_text: str, 
        delay: datetime = None, 
        buttons: str = None,
        media: str = None,
        is_published: bool = None
    ):
        url_buttons = "".join([ "".join([b.text + " - " + b.url + ("\n" if b == btn[-1] else " | ") for b in btn]) if isinstance(btn, list) else btn.text + " - " + btn.url + "\n" for btn in buttons]) if buttons else None
        await cls(
            id,
            bot_id = bot_id,
            adds_text = adds_text,
            delay = delay,
            buttons = url_buttons,
            media = media,
            is_published = is_published
        )()

class Posts(Table):
    table = "posts"
    
    @classmethod
    async def save_post(
        cls,
        id: int,
        bot_id: int,
        channel_id: str,
        post_text: str,
        hidden_extension_text_1: str = None,
        hidden_extension_text_2: str = None,
        hidden_extension_btn: str = None, 
        url_buttons: list = None,
        parse_mode: str = None,
        comments: bool = None,
        watermark: str = None,
        notify: bool = None,
        delay: datetime = None,
        media: list = None,
        autodelete: datetime = None,
        is_published: bool = None
    ):  
        
        find_media_type = lambda string: [t for t in ('photos', 'videos', 'animations') if t in string][0]
        url_buttons = "".join([ "".join([b.text + " - " + b.url + ("\n" if len(btn) == i else " | ") for i, b in enumerate(btn, 1)]) if isinstance(btn, list) else btn.text + " - " + btn.url + "\n" for btn in url_buttons])
        media = "|".join([ find_media_type(await content.get_url()) + f'/{content.file_id}' for content in media ]) if media else None 
        await cls(id, 
            bot_id = bot_id, 
            channel_id = channel_id,
            post_text = post_text,
            hidden_extension_text_1 = hidden_extension_text_1,
            hidden_extension_text_2 = hidden_extension_text_2,
            hidden_extension_btn = hidden_extension_btn,
            url_buttons = url_buttons,
            parse_mode = parse_mode,
            comments = comments,
            watermark = watermark,
            notify = notify,
            delay = delay,
            media = media,
            autodelete = autodelete,
            is_published = is_published
        )()
    @classmethod
    async def edit_post(
        cls,
        id: int,
        post_text: str = None,
        hidden_extension_text_1: str = None,
        hidden_extension_text_2: str = None,
        hidden_extension_btn: str = None, 
        url_buttons: list = None,
        parse_mode: str = None,
        comments: bool = None,
        notify: bool = None,
        watermark: str = None,
        media: str = None,
        autodelete: datetime = None
    ):
        url_buttons = "".join([ "".join([b.text + " - " + b.url + ("\n" if len(btn) == i else " | ") for i, b in enumerate(btn, 1)]) if isinstance(btn, list) else btn.text + " - " + btn.url + "\n" for btn in url_buttons])
        if media:
            if len(media) > 1:
                media = "|".join(media)
            elif len(media) == 1:
                media = media[0]
        if not media:
            media = None
        await cls.update(
            "id",
            id,
            post_text = post_text,
            hidden_extension_text_1 = hidden_extension_text_1,
            hidden_extension_text_2 = hidden_extension_text_2,
            hidden_extension_btn = hidden_extension_btn,
            url_buttons = url_buttons,
            parse_mode = parse_mode,
            comments = comments,
            notify = notify,
            watermark = watermark,
            media = media,
            autodelete = autodelete
        )

class Greetings(Table):
    table = "greetings"
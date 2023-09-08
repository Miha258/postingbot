from .main import DB
import asyncio


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
    
    @classmethod
    async def delete(cls, **kwargs):
        await posting.delete_record(cls.table, kwargs)



class Bots(Table):
    table = "bots"
    
class Paynaments(Table):
    table = "paynaments"

class Channels(Table):
    table = "channels"

class Users(Table):
    table = "users"


  

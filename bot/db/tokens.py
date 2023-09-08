from .main import DB
import asyncio


loop = asyncio.get_event_loop()
posting = loop.run_until_complete(DB("tokens.db")())


class Token:
    table = "token"

    def __init__(self, id: int, **kwargs) -> None:
        kwargs["id"] = id
        self.id = id
        self.data = kwargs

    def __str__(self) -> str:
        return f"<{self.__class__.__name__}Data {self.data}>"
    
    def __getitem__(self, key):
        return self.data[key]

    @classmethod
    async def all(cls):
        records = await posting.get_all_records(cls.table)
        return [Token(id = record["ID"], token = record["Token"], state = record["State"]) for record in records] if records else None
    



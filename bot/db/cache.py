import redis.asyncio as redis
import pickle

class PostCache():
    client = redis.StrictRedis()

    @classmethod
    async def create(cls, user_id: int, post_data: dict) -> None:
        print('Created')
        await cls.client.set(user_id, pickle.dumps(post_data))

    @classmethod
    async def update(cls, user_id: int, **kwargs) -> None:
        data = await cls.get(user_id) or {}
        for key, value in kwargs.items():
            data[key] = value
        await cls.client.set(user_id, pickle.dumps(data))
        return data


    @classmethod
    async def get(cls, uset_id: int):
        return pickle.loads(await cls.client.get(uset_id))

    @classmethod
    async def remove(cls, user_id: int):
        await cls.client.delete(user_id)
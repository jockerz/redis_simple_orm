from dataclasses import asdict
from typing import Union

from aioredis.client import Redis, Pipeline

from RSO.base import BaseModel


class Model(BaseModel):
    class Config:
        orm_mode = True

    async def is_exists(self, redis: Redis):
        return bool(await redis.exists(self.redis_key))

    def dict(self):
        return asdict(self)

    def to_redis(self):
        return self.dict()

    async def save(self, redis: Union[Pipeline, Redis]):
        if isinstance(redis, Pipeline):
            pipe = redis
        else:
            pipe = redis.pipeline()

        pipe.hmset(self.redis_key, self.to_redis())
        for index_class in self.__indexes__:
            index = index_class.create_from_model(self)
            if getattr(self, index_class.__key__) is None:
                continue
            await index.save_index(pipe)
        await pipe.execute()

    @classmethod
    async def search(cls, redis: Redis, value):
        redis_key = cls._to_redis_key(value)
        if bool(await redis.exists(redis_key)) is True:
            redis_data = await redis.hgetall(redis_key)
            return cls(**redis_data)
        else:
            return None

    async def delete(self, redis: [Pipeline, Redis]):
        if isinstance(redis, Pipeline):
            pipe = redis
        else:
            pipe = redis.pipeline()

        for index_class in self.__indexes__:
            index = index_class.create_from_model(self)
            await index.remove_from_index(pipe)

        pipe.delete(self.redis_key)
        await pipe.execute()

        del self

from typing import List, Optional, Union

from redis.asyncio.client import Redis as Redis2, Pipeline as Pipeline2
try:
    from aioredis.client import Redis, Pipeline
except (ImportError, ModuleNotFoundError):
    T_REDIS = Union[Redis2]
    T_REDIS_PIPE = Union[Redis2, Pipeline2]
    PIPE_CLS = (Pipeline2,)
else:
    T_REDIS = Union[Redis, Redis2]
    T_REDIS_PIPE = Union[Redis, Redis2, Pipeline, Pipeline2]
    PIPE_CLS = (Pipeline, Pipeline2)

from RSO.base import BaseModel


class Model(BaseModel):
    async def is_exists(self, redis: T_REDIS):
        return bool(await redis.exists(self.redis_key))

    async def save(self, redis: T_REDIS_PIPE):
        if isinstance(redis, PIPE_CLS):
            pipe = redis
        else:
            pipe = redis.pipeline()

        pipe.hset(self.redis_key, mapping=self.to_redis())

        for index_class in self.__indexes__:
            if getattr(self, index_class.__key__, None) is None:
                continue
            await index_class.save(pipe, self)

        if not isinstance(redis, (Pipeline, Pipeline2)):
            await pipe.execute()

    @classmethod
    async def search(cls, redis: T_REDIS, value) -> Optional['Model']:
        redis_key = cls.redis_key_from_value(value)
        if bool(await redis.exists(redis_key)) is True:
            fields = cls.get_fields()
            redis_data = await redis.hmget(redis_key, fields)
            dict_data = cls.from_redis(dict(zip(fields, redis_data)))
            return cls(**dict_data)
        else:
            return None

    @classmethod
    async def all(cls, redis: T_REDIS) -> List['Model']:
        redis_key = cls.redis_key_from_value('*')
        members = await redis.keys(redis_key)
        indexes = []
        for index_class in cls.__indexes__:
            indexes.append(
                f'::{index_class.__index_name__}::{index_class.__key__}'
            )
        async with redis.pipeline(transaction=True) as pipe:
            for member in members:
                is_index = False
                for index in indexes:
                    if index in member:
                        is_index = True
                        break
                if not is_index:
                    pipe.hgetall(member)
            result_data = await pipe.execute()

        result = []
        for data in result_data:
            result.append(cls(**data))
        return result


    async def delete(self, redis: T_REDIS_PIPE) -> None:
        if isinstance(redis, PIPE_CLS):
            pipe = redis
        else:
            pipe = redis.pipeline()

        for index_class in self.__indexes__:
            if getattr(self, index_class.__key__) is not None:
                await index_class.remove(pipe, self)

        pipe.delete(self.redis_key)
        if not isinstance(redis, PIPE_CLS):
            await pipe.execute()

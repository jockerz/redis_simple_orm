from datetime import date, datetime
from enum import Enum
from typing import Union

from aioredis import __version__ as aioredis_version
from aioredis.client import Redis, Pipeline
from redis.asyncio.client import Redis as Redis2, Pipeline as Pipeline2

from RSO.base import BaseModel
from .index import ListIndex


class Model(BaseModel):
    async def is_exists(self, redis: Union[Redis, Redis2]):
        return bool(await redis.exists(self.redis_key))

    async def save(self, redis: Union[Pipeline, Pipeline2, Redis, Redis2]):
        if isinstance(redis, (Pipeline, Pipeline2)):
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

    # async def extended_save(self, redis: Union[Pipeline, Pipeline2, Redis, Redis2]):
    #     """
    #     Extender of `save` method to avoid saving our key value
    #     to be saved multiple times on ListIndex
    #     """
    #     list_index_map = {}
    #     for index_class in self.__indexes__ or []:
    #         if not issubclass(index_class, ListIndex):
    #             continue
    #         model_key_value = getattr(self, self.__key__, None)
    #         if model_key_value is None:
    #             exist_on_index = False
    #         else:
    #             exist_on_index = await index_class.has_member_value(
    #                 redis, model_key_value
    #             )
    #         list_index_map[index] = exist_on_index
    #
    #     if not isinstance(redis, (Pipeline, Pipeline2)):
    #         pipe = redis
    #     else:
    #         pipe = redis.pipeline()
    #
    #     pipe.hset(self.redis_key, mapping=self.to_redis())
    #
    #     for index_class in self.__indexes__:
    #         if getattr(self, index_class.__key__, None) is None:
    #             continue
    #         await index_class.save(pipe, self)
    #
    #     # remove duplicate on index queue list
    #     for index, exist_on_index in list_index_map.items():
    #         if exist_on_index is True:
    #             model_key_value = getattr(self, self.__key__)
    #             await index.remove_from_list(pipe, model_key_value)
    #
    #     if not isinstance(redis, (Pipeline, Pipeline2)):
    #         await pipe.execute()

    @classmethod
    async def search(cls, redis: Redis, value):
        redis_key = cls.redis_key_from_value(value)
        if bool(await redis.exists(redis_key)) is True:
            fields = cls.get_fields()
            redis_data = await redis.hmget(redis_key, fields)
            dict_data = cls.from_redis(dict(zip(fields, redis_data)))
            return cls(**dict_data)
        else:
            return None

    async def delete(self, redis: [Pipeline, Pipeline2, Redis, Redis2]) -> None:
        if isinstance(redis, (Pipeline, Pipeline2)):
            pipe = redis
        else:
            pipe = redis.pipeline()

        for index_class in self.__indexes__:
            if getattr(self, index_class.__key__) is not None:
                await index_class.remove(pipe, self)

        pipe.delete(self.redis_key)
        if not isinstance(redis, (Pipeline, Pipeline2)):
            await pipe.execute()

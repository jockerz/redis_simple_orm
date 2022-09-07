from dataclasses import asdict
from datetime import date, datetime
from typing import Union

from aioredis import __version__ as aioredis_version
try:
    from aioredis.client import Redis, Pipeline
except ModuleNotFoundError:
    from aioredis.commands import Redis, Pipeline

from RSO.base import BaseModel
from .index import ListIndex


old_aioredis = aioredis_version < '2.0.0'


class Model(BaseModel):
    async def is_exists(self, redis: Redis):
        return bool(await redis.exists(self.redis_key))

    def to_redis(self):
        dict_data = self.dict()
        for key, value in self.dict().items():
            if getattr(self, key, None) is None:
                del dict_data[key]
            elif isinstance(value, bool):
                dict_data[key] = int(value)
            elif isinstance(value, (date, datetime)):
                dict_data[key] = value.isoformat()
        return dict_data

    async def save(self, redis: Union[Pipeline, Redis]):
        if isinstance(redis, Pipeline):
            pipe = redis
        else:
            pipe = redis.pipeline()

        if old_aioredis:
            pipe.hset_dict(self.redis_key, mapping=self.to_redis())
        else:
            pipe.hset(self.redis_key, mapping=self.to_redis())

        for index_class in self.__indexes__:
            index = index_class.create_from_model_class(self)
            if getattr(self, index_class.__key__, None) is None:
                continue
            await index.save_index(pipe)
        await pipe.execute()

    async def extended_save(self, redis: Union[Pipeline, Redis]):
        """
        Extender of `save` method to avoid saving our key value
        to be saved multiple times on ListIndex
        """
        list_index_map = {}
        for index_class in self.__indexes__ or []:
            if not issubclass(index_class, ListIndex):
                continue
            index = index_class.create_from_model_class(self)
            model_key_value = getattr(self, self.__key__, None)
            if model_key_value is None:
                exist_on_index = False
            else:
                exist_on_index = await index.is_exist_on_list(
                    redis, model_key_value
                )
            list_index_map[index] = exist_on_index

        if isinstance(redis, Pipeline):
            pipe = redis
        else:
            pipe = redis.pipeline()

        if old_aioredis:
            pipe.hmset_dict(self.redis_key, self.to_redis())
        else:
            pipe.hset(self.redis_key, mapping=self.to_redis())

        for index_class in self.__indexes__:
            index = index_class.create_from_model_class(self)
            if getattr(self, index_class.__key__, None) is None:
                continue
            await index.save_index(pipe)

        # remove duplicate on index queue list
        for index, exist_on_index in list_index_map.items():
            if exist_on_index is True:
                model_key_value = getattr(self, self.__key__)
                await index.remove_from_list(pipe, model_key_value)

        await pipe.execute()

    @classmethod
    async def search(cls, redis: Redis, value):
        redis_key = cls._to_redis_key(value)
        if bool(await redis.exists(redis_key)) is True:
            redis_data = await redis.hgetall(redis_key)
            dict_data = cls.from_redis(redis_data)
            return cls(**dict_data)
        else:
            return None

    async def delete(self, redis: [Pipeline, Redis]):
        if isinstance(redis, Pipeline):
            pipe = redis
        else:
            pipe = redis.pipeline()

        for index_class in self.__indexes__:
            if getattr(self, index_class.__key__) is None:
                continue
            index = index_class.create_from_model_class(self)
            await index.remove_from_index(pipe)

        pipe.delete(self.redis_key)
        await pipe.execute()

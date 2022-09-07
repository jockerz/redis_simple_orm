import typing as t
from typing import Any, Type, TypeVar, Union

from aioredis import __version__ as aioredis_version
try:
    from aioredis.client import Redis, Pipeline
    from aioredis.exceptions import ResponseError
except ModuleNotFoundError:
    from aioredis.commands import Redis, Pipeline
    from aioredis.errors import ReplyError as ResponseError

from RSO.base import BaseIndex, BaseModel


old_aioredis = aioredis_version < '2.0.0'

T = TypeVar('T')


class HashIndex(BaseIndex):

    @classmethod
    def _to_redis_key(cls):
        return f'{cls.__prefix__}::{cls.__model__.__model_name__}::'\
               f'{cls.__index_name__}::{cls.__key__}'

    @property
    def redis_key(self):
        model_prefix = self.__model__.__model_name__
        return f'{self.__prefix__}::{model_prefix}::{self.__index_name__}::'\
               f'{self.__key__}'

    async def save_index(self, redis: Pipeline):
        index_value = getattr(self.__model__, self.__key__)
        if old_aioredis:
            redis.hmset_dict(self.redis_key, {
                index_value: self._model_key_value
            })
        else:
            redis.hset(self.redis_key, mapping={
                index_value: self._model_key_value
            })

    @classmethod
    async def search_model(
        cls, redis: Redis, index_value, model_class: Type[BaseModel]
    ):
        setattr(cls, '__model__', model_class)
        redis_key = cls._to_redis_key()
        if not await redis.exists(redis_key):
            return

        model_primary_value = await redis.hmget(redis_key, index_value)
        if model_primary_value and isinstance(model_primary_value, list):
            model_primary_value = model_primary_value[0]
        return await model_class.search(redis, model_primary_value)

    async def remove_from_index(self, redis: Pipeline):
        index_value = getattr(self.__model__, self.__key__)
        redis.hdel(self.redis_key, index_value)
        del self


class ListIndex(BaseIndex):

    @classmethod
    def _to_redis_key(cls, value):
        model_prefix = cls.__model__.__model_name__
        first_part = f'{cls.__prefix__}::{model_prefix}::'\
                     f'{cls.__index_name__}::{cls.__key__}'
        return f'{first_part}:{value}'

    @property
    def redis_key(self):
        value = getattr(self.__model__, self.__key__)
        return self._to_redis_key(value)

    async def save_index(self, redis: Pipeline):
        redis.lpush(self.redis_key, self._model_key_value)

    @classmethod
    async def get_members(cls, redis: Redis, index_value):
        redis_key = cls._to_redis_key(index_value)
        return await redis.lrange(redis_key, 0, -1)

    async def is_exist_on_list(self, redis: Redis, model_value: Any):
        try:
            if hasattr(redis, 'lpos'):
                result = await redis.lpos(self.redis_key, model_value)
            else:
                result = await redis.execute('LPOS', self.redis_key, model_value)
            return result is not None
        except (AttributeError, ResponseError):
            items = await redis.lrange(self.redis_key, 0, -1)
            return model_value in items or str(model_value) in items

    async def remove_from_list(
        self, redis: Union[Pipeline, Redis], model_value: T,
        count: int = 1
    ):
        """
        count = 0 to delete all
        """
        if isinstance(redis, Pipeline):
            redis.lrem(self.redis_key, count, model_value)
        else:
            await redis.lrem(self.redis_key, count, model_value)

    @classmethod
    async def search_models(cls, redis: Redis, index_value, model_class: Type[BaseModel]):
        setattr(cls, '__model__', model_class)
        redis_key = cls._to_redis_key(index_value)
        if not bool(await redis.exists(redis_key)):
            return []

        model_instances = []
        for value in (await redis.lrange(redis_key, 0, -1)):
            model_instance = await model_class.search(redis, value)
            model_instances.append(model_instance)
        return model_instances

    async def remove_from_index(self, redis: Pipeline, count: int = 1):
        """
        count = 0 to remove all
        """
        redis.lrem(self.redis_key, count, self._model_key_value)

    @classmethod
    async def get_by_rpoplpush(cls, redis, index_value, model_class: Type[BaseModel]):
        redis_key = cls._to_redis_key(index_value)
        if bool(await redis.exists(redis_key)) is False:
            return
        else:
            model_value = await redis.rpoplpush(redis_key, redis_key)
            return await model_class.search(redis, model_value)


class SetIndex(BaseIndex):

    @classmethod
    def _to_redis_key(cls, value):
        model_prefix = cls.__model__.__model_name__
        first_part = f'{cls.__prefix__}::{model_prefix}::'\
                     f'{cls.__index_name__}::{cls.__key__}'
        return f'{first_part}:{value}'

    @property
    def redis_key(self):
        value = getattr(self.__model__, self.__key__)
        return self._to_redis_key(value)

    async def save_index(self, redis: Pipeline):
        redis.sadd(self.redis_key, self._model_key_value)

    @classmethod
    async def get_members(cls, redis: Redis, index_value):
        redis_key = cls._to_redis_key(index_value)
        return await redis.smembers(redis_key)

    @classmethod
    async def search_models(
        cls, redis: Redis, index_value, model_class: Type[BaseModel]
    ):
        setattr(cls, '__model__', model_class)
        redis_key = cls._to_redis_key(index_value)
        if not bool(await redis.exists(redis_key)):
            return []

        model_instances = []
        for value in (await redis.smembers(redis_key)):
            model_instance = await model_class.search(redis, value)
            model_instances.append(model_instance)
        return model_instances

    async def remove_from_index(self, redis: Pipeline):
        redis.srem(self.redis_key, self._model_key_value)

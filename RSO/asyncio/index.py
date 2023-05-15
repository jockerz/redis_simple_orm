from typing import Any, Optional, TypeVar, Union

from aioredis.client import Redis, Pipeline
from redis.asyncio.client import Redis as Redis2, Pipeline as Pipeline2
from RSO.base import BaseModel, BaseHashIndex, BaseListIndex, BaseSetIndex

T = TypeVar('T')


class HashIndex(BaseHashIndex):
    @classmethod
    async def save(
        cls, redis: Union[Pipeline, Pipeline2], model_obj: T
    ) -> None:
        index_value = getattr(model_obj, cls.__key__)
        redis.hset(cls.redis_key(), mapping={
            index_value: cls.model_key_value(model_obj)
        })

    @classmethod
    async def remove(
        cls, redis: Union[Pipeline, Pipeline2], model_obj: T
    ) -> None:
        redis.hdel(cls.redis_key(), cls.index_key_value(model_obj))

    @classmethod
    async def search_model(cls, redis: Union[Redis, Redis2], index_value):
        redis_key = cls.redis_key()
        if not bool(await redis.exists(redis_key)):
            return

        model_key_value = await redis.hmget(redis_key, index_value)
        if model_key_value and isinstance(model_key_value, list):
            model_key_value = model_key_value[0]
        return await cls.__model__.search(redis, model_key_value)


class ListIndex(BaseListIndex):
    @classmethod
    async def save(
        cls, redis: Union[Pipeline, Pipeline2], model_obj: T
    ) -> None:
        redis.lpush(cls.redis_key(model_obj), cls.model_key_value(model_obj))

    @classmethod
    async def remove(
        cls, redis: Union[Pipeline, Pipeline2], model_obj: T, count: int = 1
    ):
        """count = 0 to remove all"""
        redis.lrem(
            cls.redis_key(model_obj),
            count,
            cls.model_key_value(model_obj)
        )

    @classmethod
    async def get_members(cls, redis: Redis, index_value):
        redis_key = cls.redis_key_from_value(index_value)
        return await redis.lrange(redis_key, 0, -1)

    @classmethod
    async def search_models(cls, redis: Redis, index_value):
        redis_key = cls.redis_key_from_value(index_value)
        if not bool(await redis.exists(redis_key)):
            return []

        model_instances = []
        for value in (await redis.lrange(redis_key, 0, -1)):
            model_instance = await cls.__model__.search(redis, value)
            model_instances.append(model_instance)
        return model_instances

    @classmethod
    async def has_member(cls, redis: [Redis, Redis2], model_obj: T) -> bool:
        return await cls.has_member_value(
            redis,
            getattr(model_obj, cls.__key__),
            getattr(model_obj, model_obj.__key__)
        )

    @classmethod
    async def has_member_value(
        cls, redis: [Redis, Redis2], index_value: Any, model_value: Any
    ) -> bool:
        if hasattr(redis, 'lpos'):
            result = await redis.lpos(
                cls.redis_key_from_value(index_value),
                model_value
            )
        else:
            result = await redis.execute(
                'LPOS',
                cls.redis_key_from_value(index_value),
                model_value
            )
        return result is not None

    @classmethod
    async def get_by_rpoplpush(
        cls, redis: [Redis, Redis2], index_value: Any,
    ) -> Optional[BaseModel]:
        redis_key = cls.redis_key_from_value(index_value)
        if bool(await redis.exists(redis_key)) is False:
            return
        else:
            model_value = await redis.rpoplpush(redis_key, redis_key)
            return await cls.__model__.search(redis, model_value)


class SetIndex(BaseSetIndex):
    @classmethod
    async def save(cls, redis: [Pipeline, Pipeline2], model_obj: T) -> None:
        redis.sadd(
            cls.redis_key(model_obj),
            cls.model_key_value(model_obj)
        )

    @classmethod
    async def remove(cls, redis: [Pipeline, Pipeline2], model_obj: T) -> None:
        redis.srem(
            cls.redis_key(model_obj),
            cls.model_key_value(model_obj)
        )

    @classmethod
    async def get_members(cls, redis: Redis, index_value):
        redis_key = cls.redis_key_from_value(index_value)
        return await redis.smembers(redis_key)

    @classmethod
    async def search_models(cls, redis: Redis, index_value):
        redis_key = cls.redis_key_from_value(index_value)
        if not bool(await redis.exists(redis_key)):
            return []

        model_instances = []
        for value in (await redis.smembers(redis_key)):
            model_instance = await cls.__model__.search(redis, value)
            model_instances.append(model_instance)
        return model_instances

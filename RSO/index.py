from typing import Any, List, Optional, TypeVar, Union

from redis.client import Pipeline, Redis

from .base import BaseModel, BaseHashIndex, BaseListIndex, BaseSetIndex

T = TypeVar('T')


class HashIndex(BaseHashIndex):
    @classmethod
    def save(
        cls, redis: Union[Pipeline, Redis], model_obj: T
    ) -> None:
        redis.hset(
            cls.redis_key(),
            cls.index_key_value(model_obj),
            cls.model_key_value(model_obj)
        )

    @classmethod
    def remove(
        cls, redis: Union[Pipeline, Redis], model_obj: T
    ) -> None:
        redis.hdel(cls.redis_key(), cls.index_key_value(model_obj))

    @classmethod
    def search_model(cls, redis: Redis, index_value) -> Optional[BaseModel]:
        redis_key = cls.redis_key()
        if bool(not redis.exists(redis_key)):
            return

        model_key_value = redis.hmget(redis_key, index_value)
        if isinstance(model_key_value, list):
            model_key_value = model_key_value[0]
        return cls.__model__.search(redis, model_key_value)


class ListIndex(BaseListIndex):
    @classmethod
    def save(
        cls, redis: Union[Pipeline, Redis], model_obj: T
    ) -> None:
        redis.lpush(
            cls.redis_key(model_obj),
            cls.model_key_value(model_obj)
        )

    @classmethod
    def remove(cls, redis: Redis, model_obj: T, count: int = 1) -> None:
        """count = 0 to remove all"""
        redis.lrem(
            cls.redis_key(model_obj),
            count,
            cls.model_key_value(model_obj)
        )

    @classmethod
    def get_members(
        cls, redis: Union[Pipeline, Redis], index_value: Any
    ) -> List[Any]:
        return redis.lrange(cls.redis_key_from_value(index_value), 0, -1)

    @classmethod
    def search_models(cls, redis: Redis, index_value: Any) -> List[BaseModel]:
        redis_key = cls.redis_key_from_value(index_value)
        if not redis.exists(redis_key):
            return []

        instance_list = []
        for value in cls.get_members(redis, index_value):
            instance = cls.__model__.search(redis, value)
            instance_list.append(instance)
        return instance_list

    @classmethod
    def has_member(cls, redis: Redis, model_obj: T) -> bool:
        return cls.has_member_value(
            redis,
            getattr(model_obj, cls.__key__),
            getattr(model_obj, model_obj.__key__)
        )

    @classmethod
    def has_member_value(
        cls, redis: Redis, index_value: Any, model_value: Any
    ) -> bool:
        result = redis.lpos(
            cls.redis_key_from_value(index_value),
            model_value
        )
        return result is not None

    @classmethod
    def get_by_rpoplpush(
        cls, redis: Redis, index_value: Any
    ) -> Optional[BaseModel]:
        redis_key = cls.redis_key_from_value(index_value)
        if redis.exists(redis_key) == 0:
            return None
        else:
            value = redis.rpoplpush(redis_key, redis_key)
            return cls.__model__.search(redis, value)


class SetIndex(BaseSetIndex):
    @classmethod
    def save(
        cls, redis: Union[Pipeline, Redis], model_obj: T
    ) -> None:
        redis.sadd(
            cls.redis_key(model_obj),
            cls.model_key_value(model_obj)
        )

    @classmethod
    def remove(cls, redis: Union[Pipeline, Redis], model_obj: T):
        redis.srem(cls.redis_key(model_obj), cls.model_key_value(model_obj))

    @classmethod
    def get_members(cls, redis: Redis, index_value) -> List[Any]:
        redis_key = cls.redis_key_from_value(index_value)
        return redis.smembers(redis_key)

    @classmethod
    def search_models(cls, redis: Redis, index_value) -> List[BaseModel]:
        redis_key = cls.redis_key_from_value(index_value)
        if not redis.exists(redis_key):
            return []

        model_instances = []
        for value in redis.smembers(redis_key):
            model_instance = cls.__model__.search(redis, value)
            model_instances.append(model_instance)
        return model_instances

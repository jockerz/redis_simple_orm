from typing import Any, List, Optional, Type, TypeVar, Union

from redis.client import Pipeline, Redis

from .base import BaseIndex, BaseModel

T = TypeVar('T')


class HashIndex(BaseIndex):
    @classmethod
    def _to_redis_key(cls) -> str:
        return f'{cls.__prefix__}::{cls.__model__.__model_name__}::'\
               f'{cls.__index_name__}::{cls.__key__}'

    @property
    def redis_key(self) -> str:
        return self._to_redis_key()

    def save_index(self, redis: Union[Pipeline, Redis]) -> None:
        index_value = getattr(self.__model__, self.__key__)
        redis.hset(self.redis_key, index_value, self._model_key_value)

    @classmethod
    def search_model(
        cls, redis: Redis, index_value, model_class: Type[BaseModel]
    ) -> Optional[BaseModel]:
        setattr(cls, '__model__', model_class)
        redis_key = cls._to_redis_key()
        if not redis.exists(redis_key):
            return

        model_primary_value = redis.hmget(redis_key, index_value)
        if isinstance(model_primary_value, list):
            model_primary_value = model_primary_value[0]
        return model_class.search(redis, model_primary_value)

    def remove_from_index(self, redis: Union[Pipeline, Redis]):
        index_value = getattr(self.__model__, self.__key__)
        redis.hdel(self.redis_key, index_value)
        del self


class ListIndex(BaseIndex):
    @classmethod
    def _to_redis_key(cls, value) -> str:
        model_prefix = cls.__model__.__model_name__
        first_part = f'{cls.__prefix__}::{model_prefix}::'\
                     f'{cls.__index_name__}::{cls.__key__}'
        return f'{first_part}:{value}'

    @property
    def redis_key(self) -> str:
        value = getattr(self.__model__, self.__key__)
        return self._to_redis_key(value)

    def save_index(self, redis: Union[Pipeline, Redis]) -> None:
        redis.lpush(self.redis_key, self._model_key_value)

    def remove_from_list(
        self, redis: Union[Pipeline, Redis], model_value: Any,
        count: int = 1
    ) -> None:
        """
        count = 0 to delete all
        """
        redis.lrem(self.redis_key, count, model_value)

    @classmethod
    def get_members(
        cls, redis: Union[Pipeline, Redis], index_value: Any
    ) -> List[Any]:
        return redis.lrange(cls._to_redis_key(index_value), 0, -1)

    @classmethod
    def search_models(
        cls, redis: Redis, index_value: Any, model_class: T
    ) -> List[BaseModel]:
        setattr(cls, '__model__', model_class)
        redis_key = cls._to_redis_key(index_value)
        if not redis.exists(redis_key):
            return []

        instance_list = []
        for value in cls.get_members(redis, index_value):
            instance = model_class.search(redis, value)
            instance_list.append(instance)
        return instance_list

    def is_exist_on_list(self, redis: Redis, model_value: Any) -> bool:
        result = redis.execute_command('LPOS', self.redis_key, model_value)
        return result is not None

    @classmethod
    def get_by_rpoplpush(
        cls, redis: Redis, index_value: Any, model_class: Type[BaseModel]
    ) -> Optional[BaseModel]:
        cls.__model__ = model_class
        redis_key = cls._to_redis_key(index_value)
        if redis.exists(redis_key) == 0:
            return None
        else:
            value = redis.rpoplpush(redis_key, redis_key)
            return model_class.search(redis, value)

    def remove_from_index(self, redis: Redis, count: int = 1) -> None:
        """
        count = 0 to remove all
        """
        redis.lrem(self.redis_key, count, self._model_key_value)


class SetIndex(BaseIndex):

    @classmethod
    def _to_redis_key(cls, value: Any) -> str:
        model_prefix = cls.__model__.__model_name__
        first_part = f'{cls.__prefix__}::{model_prefix}::'\
                     f'{cls.__index_name__}::{cls.__key__}'
        return f'{first_part}:{value}'

    @property
    def redis_key(self) -> str:
        value = getattr(self.__model__, self.__key__)
        return self._to_redis_key(value)

    def save_index(self, redis: Union[Pipeline, Redis]) -> None:
        redis.sadd(self.redis_key, self._model_key_value)

    @classmethod
    def get_members(cls, redis: Redis, index_value) -> List[Any]:
        redis_key = cls._to_redis_key(index_value)
        return redis.smembers(redis_key)

    @classmethod
    def search_models(
        cls, redis: Redis, index_value, model_class: Type[BaseModel]
    ) -> List[BaseModel]:
        setattr(cls, '__model__', model_class)
        redis_key = cls._to_redis_key(index_value)
        if not redis.exists(redis_key):
            return []

        model_instances = []
        for value in redis.smembers(redis_key):
            model_instance = model_class.search(redis, value)
            model_instances.append(model_instance)
        return model_instances

    def remove_from_index(self, redis: Union[Pipeline, Redis]):
        redis.srem(self.redis_key, self._model_key_value)

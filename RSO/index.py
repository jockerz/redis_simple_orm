from typing import Union

from redis.client import Pipeline, Redis

from .base import BaseIndex, BaseModel


class HashIndex(BaseIndex):

    @property
    def redis_key(self):
        model_prefix = self.__model__.__model_name__
        return f'{self.__prefix__}::{model_prefix}::{self.__index_name__}::'\
               f'{self.__key__}'

    def save_index(self, redis: Union[Pipeline, Redis]):
        index_value = getattr(self.__model__, self.__key__)
        redis.hmset(self.redis_key, {index_value: self._model_key_value})

    @classmethod
    def search_model(cls, redis: Redis, index_value, model_class: BaseModel):
        index = cls.create_from_model(model_class)
        if not redis.exists(index.redis_key):
            return

        model_primary_value = redis.hmget(index.redis_key, index_value)
        if isinstance(model_primary_value, list):
            model_primary_value = model_primary_value[0]
        return model_class.search(redis, model_primary_value)

    def remove_from_index(self, redis: Union[Pipeline, Redis]):
        index_value = getattr(self.__model__, self.__key__)
        redis.hdel(self.redis_key, index_value)
        del self


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

    def save_index(self, redis: Union[Pipeline, Redis]):
        redis.sadd(self.redis_key, self._model_key_value)

    @classmethod
    def get_members(cls, redis: Redis, index_value):
        redis_key = cls._to_redis_key(index_value)
        return redis.smembers(redis_key)

    @classmethod
    def search_models(cls, redis: Redis, index_value, model_class: BaseModel):
        index = cls.create_from_model(model_class)
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

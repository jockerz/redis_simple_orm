from typing import Any, Union, Type, TypeVar

from txredisapi import BaseRedisProtocol, ConnectionHandler
from twisted.internet.defer import inlineCallbacks, returnValue

from RSO.base import BaseIndex, BaseModel

T = TypeVar('T')


class HashIndex(BaseIndex):
    @classmethod
    def _to_redis_key(cls) -> str:
        return f'{cls.__prefix__}::{cls.__model__.__model_name__}::'\
               f'{cls.__index_name__}::{cls.__key__}'

    @property
    def redis_key(self) -> str:
        return self._to_redis_key()

    @inlineCallbacks
    def save_index(self, redis: Union[BaseRedisProtocol, ConnectionHandler]):
        index_value = getattr(self.__model__, self.__key__)
        if isinstance(redis, BaseRedisProtocol):
            redis.hmset(
                self.redis_key, {index_value: self._model_key_value}
            )
            returnValue(None)
        else:
            yield redis.hmset(
                self.redis_key, {index_value: self._model_key_value}
            )

    @classmethod
    @inlineCallbacks
    def search_model(
        cls, redis: ConnectionHandler, index_value, model_class: Type[BaseModel]
    ):
        setattr(cls, '__model__', model_class)
        redis_key = cls._to_redis_key()
        is_exist = yield redis.exists(redis_key)
        if not is_exist:
            return
        model_primary_value = yield redis.hget(redis_key, index_value)
        if model_primary_value is None:
            return
        result = yield model_class.search(redis, model_primary_value)
        returnValue(result)

    @inlineCallbacks
    def remove_from_index(
        self, redis: Union[BaseRedisProtocol, ConnectionHandler]
    ):
        index_value = getattr(self.__model__, self.__key__)
        yield redis.hdel(self.redis_key, index_value)
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

    @inlineCallbacks
    def save_index(self, redis: Union[BaseRedisProtocol, ConnectionHandler]):
        if isinstance(redis, BaseRedisProtocol):
            redis.lpush(self.redis_key, self._model_key_value)
            returnValue(None)
        else:
            yield redis.lpush(self.redis_key, self._model_key_value)

    @classmethod
    @inlineCallbacks
    def get_members(cls, redis: ConnectionHandler, index_value: Any):
        redis_key = cls._to_redis_key(index_value)
        result = yield redis.lrange(redis_key, 0, -1)
        return result

    @inlineCallbacks
    def is_exist_on_list(
        self, redis: ConnectionHandler, model_value: BaseModel
    ):
        result = yield redis.execute_command(
            "LPOS", self.redis_key, model_value
        )
        return result is not None

    @inlineCallbacks
    def remove_from_list(
        self, redis: Union[BaseRedisProtocol, ConnectionHandler],
        model_value: Any, count: int = 1
    ):
        """
        count = 0 to delete all
        """
        if isinstance(redis, ConnectionHandler):
            yield redis.lrem(self.redis_key, count, model_value)
        else:
            redis.lrem(self.redis_key, count, model_value)

    @classmethod
    @inlineCallbacks
    def search_models(
        cls, redis: ConnectionHandler, index_value, model_class: T
    ):
        setattr(cls, '__model__', model_class)
        redis_key = cls._to_redis_key(index_value)
        result = yield redis.exists(redis_key)
        if not result:
            return []

        model_instances = []
        result = yield redis.lrange(redis_key, 0, -1)
        for value in result:
            model_instance = yield model_class.search(redis, value)
            model_instances.append(model_instance)
        return model_instances

    @inlineCallbacks
    def remove_from_index(
        self, redis: Union[BaseRedisProtocol, ConnectionHandler],
        count: int = 1
    ):
        """
        count = 0 to remove all
        """
        yield redis.lrem(self.redis_key, count, self._model_key_value)

    @classmethod
    @inlineCallbacks
    def get_by_rpoplpush(cls, redis, index_value, model_class: Type[BaseModel]):
        cls.__model__ = model_class
        redis_key = cls._to_redis_key(index_value)
        result = yield redis.exists(redis_key)
        if not result:
            returnValue(None)
        else:
            value = yield redis.rpoplpush(redis_key, redis_key)
            result = yield model_class.search(redis, value)
            returnValue(result)


class SetIndex(BaseIndex):

    @classmethod
    def _to_redis_key(cls, value):
        first_part = f'{cls.__prefix__}::{cls.__model__.__model_name__}::'\
                     f'{cls.__index_name__}::{cls.__key__}'
        return f'{first_part}:{value}'

    @property
    def redis_key(self):
        value = getattr(self.__model__, self.__key__)
        return self._to_redis_key(value)

    @inlineCallbacks
    def save_index(self, redis: Union[BaseRedisProtocol, ConnectionHandler]):
        if isinstance(redis, BaseRedisProtocol):
            redis.sadd(self.redis_key, self._model_key_value)
            returnValue(None)
        else:
            yield redis.sadd(self.redis_key, self._model_key_value)

    @classmethod
    @inlineCallbacks
    def get_members(cls, redis: ConnectionHandler, index_value):
        redis_key = cls._to_redis_key(index_value)
        result = yield redis.smembers(redis_key)
        return returnValue(result)

    @classmethod
    @inlineCallbacks
    def search_models(
        cls, redis: ConnectionHandler, index_value, model_class: Type[BaseModel]
    ):
        setattr(cls, '__model__', model_class)
        redis_key = cls._to_redis_key(index_value)
        result = yield redis.exists(redis_key)
        if not result:
            return []

        model_instances = []
        result = yield redis.smembers(redis_key)
        for value in result:
            model_instance = yield model_class.search(redis, value)
            model_instances.append(model_instance)
        return model_instances

    @inlineCallbacks
    def remove_from_index(self, redis: Union[BaseRedisProtocol, ConnectionHandler]):
        yield redis.srem(self.redis_key, self._model_key_value)

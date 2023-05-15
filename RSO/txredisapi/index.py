from typing import Any, List, Optional, Union, TypeVar

from txredisapi import BaseRedisProtocol, ConnectionHandler
from twisted.internet.defer import inlineCallbacks, returnValue

from RSO.base import BaseModel, BaseHashIndex, BaseListIndex, BaseSetIndex

T = TypeVar('T')


class HashIndex(BaseHashIndex):
    @classmethod
    @inlineCallbacks
    def save(
        cls, redis: Union[BaseRedisProtocol, ConnectionHandler], model_obj: T
    ):
        index_value = cls.index_key_value(model_obj)
        if isinstance(redis, BaseRedisProtocol):
            redis.hmset(
                cls.redis_key(),
                {index_value: cls.model_key_value(model_obj)}
            )
            returnValue(None)
        else:
            yield redis.hmset(
                cls.redis_key(),
                {index_value: cls.model_key_value(model_obj)}
            )

    @classmethod
    @inlineCallbacks
    def remove(
        cls, redis: Union[BaseRedisProtocol, ConnectionHandler], model_obj: T
    ):
        yield redis.hdel(
            cls.redis_key(),
            cls.index_key_value(model_obj)
        )

    @classmethod
    @inlineCallbacks
    def search_model(cls, redis: ConnectionHandler, index_value):
        redis_key = cls.redis_key()
        is_exist = yield redis.exists(redis_key)
        if not is_exist:
            return
        model_primary_value = yield redis.hget(redis_key, index_value)
        if model_primary_value is None:
            return
        result = yield cls.__model__.search(redis, model_primary_value)
        returnValue(result)


class ListIndex(BaseListIndex):
    @classmethod
    @inlineCallbacks
    def save(
        cls, redis: Union[BaseRedisProtocol, ConnectionHandler], model_obj: T
    ):
        if isinstance(redis, BaseRedisProtocol):
            redis.lpush(
                cls.redis_key(model_obj),
                cls.model_key_value(model_obj)
            )
            returnValue(None)
        else:
            yield redis.lpush(
                cls.redis_key(model_obj),
                cls.model_key_value(model_obj)
            )

    @classmethod
    @inlineCallbacks
    def remove(
        cls, redis: Union[BaseRedisProtocol, ConnectionHandler],
        model_obj: T, count: int = 1
    ):
        """
        count = 0 to remove all
        """
        yield redis.lrem(
            cls.redis_key(model_obj),
            count,
            cls.model_key_value(model_obj)
        )

    @classmethod
    @inlineCallbacks
    def search_models(
        cls, redis: ConnectionHandler, index_value: Any
    ) -> List[BaseModel]:
        redis_key = cls.redis_key_from_value(index_value)
        result = yield redis.exists(redis_key)
        if not result:
            return []

        model_instances = []
        result = yield cls.get_members(redis, index_value)
        for value in result:
            model_instance = yield cls.__model__.search(redis, value)
            model_instances.append(model_instance)
        return model_instances

    @classmethod
    @inlineCallbacks
    def get_members(
        cls, redis: ConnectionHandler, index_value: Any
    ) -> List[Any]:
        redis_key = cls.redis_key_from_value(index_value)
        result = yield redis.lrange(redis_key, 0, -1)
        return result

    @classmethod
    @inlineCallbacks
    def has_member(cls, redis: ConnectionHandler, model_obj: T) -> bool:
        result = yield cls.has_member_value(
            redis,
            getattr(model_obj, cls.__key__),
            getattr(model_obj, model_obj.__key__)
        )
        return result

    @classmethod
    @inlineCallbacks
    def has_member_value(
        cls, redis: ConnectionHandler, index_value: Any, model_value: Any
    ) -> bool:
        result = yield redis.execute_command(
            'LPOS',
            cls.redis_key_from_value(index_value),
            model_value
        )
        return result is not None

    @classmethod
    @inlineCallbacks
    def get_by_rpoplpush(cls, redis, index_value) -> Optional[BaseModel]:
        redis_key = cls.redis_key_from_value(index_value)
        result = yield redis.exists(redis_key)
        if not result:
            returnValue(None)
        else:
            value = yield redis.rpoplpush(redis_key, redis_key)
            result = yield cls.__model__.search(redis, value)
            returnValue(result)


class SetIndex(BaseSetIndex):
    @classmethod
    @inlineCallbacks
    def save(
        cls, redis: Union[BaseRedisProtocol, ConnectionHandler], model_obj: T
    ):
        if isinstance(redis, BaseRedisProtocol):
            redis.sadd(
                cls.redis_key(model_obj),
                cls.model_key_value(model_obj)
            )
            returnValue(None)
        else:
            yield redis.sadd(
                cls.redis_key(model_obj),
                members=cls.model_key_value(model_obj)
            )

    @classmethod
    @inlineCallbacks
    def remove(
        cls, redis: Union[BaseRedisProtocol, ConnectionHandler], model_obj: T
    ):
        yield redis.srem(
            cls.redis_key(model_obj),
            members=cls.model_key_value(model_obj)
        )

    @classmethod
    @inlineCallbacks
    def get_members(
        cls, redis: ConnectionHandler, index_value: Any
    ) -> List[Any]:
        redis_key = cls.redis_key_from_value(index_value)
        result = yield redis.smembers(redis_key)
        return returnValue(result)

    @classmethod
    @inlineCallbacks
    def search_models(
        cls, redis: ConnectionHandler, index_value: Any
    ) -> List[BaseModel]:
        redis_key = cls.redis_key_from_value(index_value)
        result = yield redis.exists(redis_key)
        if not result:
            return []

        model_instances = []
        result = yield redis.smembers(redis_key)
        for value in result:
            model_instance = yield cls.__model__.search(redis, value)
            model_instances.append(model_instance)
        return model_instances

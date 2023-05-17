from typing import List, Optional, Union

from txredisapi import BaseRedisProtocol, ConnectionHandler
from twisted.internet.defer import inlineCallbacks

from RSO.base import BaseModel


class Model(BaseModel):
    @inlineCallbacks
    def is_exist(self, redis: ConnectionHandler):
        result = yield redis.exists(self.redis_key)
        return bool(result)

    @inlineCallbacks
    def save(self, redis: Union[BaseRedisProtocol, ConnectionHandler]):
        if isinstance(redis, ConnectionHandler):
            pipe = yield redis.multi()
            do_commit = True
        else:
            pipe = redis
            do_commit = False

        pipe.hmset(self.redis_key, self.to_redis())
        for index_class in self.__indexes__ or []:
            if getattr(self, index_class.__key__, None) is None:
                continue
            yield index_class.save(pipe, self)
        if do_commit:
            yield pipe.commit()

    @classmethod
    @inlineCallbacks
    def search(cls, redis: ConnectionHandler, value) -> Optional['Model']:
        redis_key = cls.redis_key_from_value(value)
        result = yield redis.exists(redis_key)
        if bool(result):
            fields = cls.get_fields()
            redis_data = yield redis.hmget(redis_key, fields)
            dict_data = cls.from_redis(dict(zip(fields, redis_data)))
            return cls(**dict_data)
        return

    @classmethod
    @inlineCallbacks
    def all(cls, redis: ConnectionHandler) -> List['Model']:
        redis_key = cls.redis_key_from_value('*')
        members = yield redis.keys(redis_key)
        indexes = []
        for index_class in cls.__indexes__:
            indexes.append(
                f'::{index_class.__index_name__}::{index_class.__key__}'
            )

        pipe = yield redis.multi()
        for member in members:
            is_index = False
            for index in indexes:
                if index in member:
                    is_index = True
                    break
            if not is_index:
                yield pipe.hgetall(member)
        result_data = yield pipe.commit()

        result = []
        for data in result_data:
            result.append(cls(**data))
        return result

    @inlineCallbacks
    def delete(self, redis: Union[BaseRedisProtocol, ConnectionHandler]):
        if isinstance(redis, ConnectionHandler):
            pipe = yield redis.multi()
            do_commit = True
        else:
            pipe = redis
            do_commit = False

        for index_class in self.__indexes__ or []:
            if getattr(self, index_class.__key__) is None:
                continue
            index_class.remove(pipe, self)
        yield pipe.delete(self.redis_key)
        if do_commit:
            yield pipe.commit()

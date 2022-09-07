from typing import Union

from dataclasses import asdict
from txredisapi import BaseRedisProtocol, ConnectionHandler
from twisted.internet.defer import inlineCallbacks

from RSO.base import BaseModel
from .index import ListIndex


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
            index = index_class.create_from_model_class(self)
            yield index.save_index(pipe)
        if do_commit:
            yield pipe.commit()

    @inlineCallbacks
    def extended_save(
        self, redis: Union[BaseRedisProtocol, ConnectionHandler]
    ):
        """Extended save function to avoid multiple push on list index

        Note: Use this method if you use List Index
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
                exist_on_index = yield index.is_exist_on_list(
                    redis, model_key_value
                )
            list_index_map[index] = exist_on_index

        if isinstance(redis, ConnectionHandler):
            pipe = yield redis.multi()
        else:
            raise NotImplementedError

        pipe.hmset(self.redis_key, self.to_redis())
        for index_class in self.__indexes__ or []:
            if getattr(self, index_class.__key__, None) is None:
                continue
            index = index_class.create_from_model_class(self)
            yield index.save_index(pipe)

        # remove duplicate on index queue list
        for index, exist_on_index in list_index_map.items():
            if exist_on_index is True:
                model_key_value = getattr(self, self.__key__)
                yield index.remove_from_list(pipe, model_key_value)

        yield pipe.commit()

    @classmethod
    @inlineCallbacks
    def search(cls, redis: ConnectionHandler, value):
        redis_key = cls._to_redis_key(value)
        result = yield redis.exists(redis_key)
        if bool(result):
            redis_data = yield redis.hgetall(redis_key)
            dict_data = cls.from_redis(redis_data)
            return cls(**dict_data)
        return

    @inlineCallbacks
    def delete(self, redis: Union[BaseRedisProtocol, ConnectionHandler]):
        if isinstance(redis, ConnectionHandler):
            pipe = yield redis.multi()
        else:
            raise NotImplementedError
        for index_class in self.__indexes__ or []:
            if getattr(self, index_class.__key__) is None:
                continue
            index = index_class.create_from_model_class(self)
            index.remove_from_index(pipe)
        pipe.delete(self.redis_key)
        yield pipe.commit()

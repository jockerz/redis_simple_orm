from typing import Union

from dataclasses import asdict
from txredisapi import BaseRedisProtocol, ConnectionHandler
from twisted.internet.defer import inlineCallbacks, returnValue

from RSO.base import BaseModel
from .index import ListIndex


class Model(BaseModel):
    @inlineCallbacks
    def is_exist(self, redis: ConnectionHandler):
        result = yield redis.exists(self.redis_key)
        returnValue(bool(result))

    @inlineCallbacks
    def save(self, redis: Union[BaseRedisProtocol, ConnectionHandler]):
        if isinstance(redis, ConnectionHandler):
            pipe = yield redis.multi()
        else:
            raise NotImplementedError

        pipe.hmset(self.redis_key, self.to_redis())
        for index_class in self.__indexes__ or []:
            if getattr(self, index_class.__key__, None) is None:
                continue
            index = index_class.create_from_model(self)
            yield index.save_index(pipe)
        yield pipe.commit()

    @inlineCallbacks
    def extended_save(
        self, redis: Union[BaseRedisProtocol, ConnectionHandler]
    ):
        """extended save function to avoid multiple push on list index"""
        list_index_map = {}
        for index_class in self.__indexes__ or []:
            if not issubclass(index_class, ListIndex):
                continue
            index = index_class.create_from_model(self)
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
            index = index_class.create_from_model(self)
            yield index.save_index(pipe)

        # avoid duplicate on index queue list
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
            returnValue(cls(**redis_data))
        else:
            returnValue(None)

    def dict(self):
        return asdict(self)

    def to_redis(self):
        dict_data = self.dict()
        for key, value in dict_data.copy().items():
            if value is None:
                del dict_data[key]
        return dict_data

    @inlineCallbacks
    def delete(self, redis: Union[BaseRedisProtocol, ConnectionHandler]):
        if isinstance(redis, ConnectionHandler):
            pipe = yield redis.multi()
        else:
            raise NotImplementedError
        for index_class in self.__indexes__ or []:
            if getattr(self, index_class.__key__) is None:
                continue
            index = index_class.create_from_model(self)
            index.remove_from_index(pipe)
        pipe.delete(self.redis_key)
        yield pipe.commit()

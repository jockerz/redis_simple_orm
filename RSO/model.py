from typing import List, Optional, Union

from redis.client import Pipeline, Redis

from RSO.base import BaseModel


class Model(BaseModel):
    def is_exists(self, redis: Redis):
        return bool(redis.exists(self.redis_key))

    def save(self, redis: Union[Pipeline, Redis]):
        if isinstance(redis, Pipeline):
            pipe = redis
        else:
            pipe = redis.pipeline()

        pipe.hset(self.redis_key, mapping=self.to_redis())
        for index_class in self.__indexes__ or []:
            if getattr(self, index_class.__key__) is None:
                continue
            index_class.save(pipe, self)

        if not isinstance(redis, Pipeline):
            pipe.execute()

    @classmethod
    def search(cls, redis: Redis, value) -> Optional['Model']:
        redis_key = cls.redis_key_from_value(value)
        if bool(redis.exists(redis_key)):
            fields = cls.get_fields()
            redis_data = redis.hmget(redis_key, fields)
            dict_data = cls.from_redis(dict(zip(fields, redis_data)))
            return cls(**dict_data)
        else:
            return None

    @classmethod
    def all(cls, redis: Redis) -> List['Model']:
        redis_key = cls.redis_key_from_value('*')
        members = redis.keys(redis_key)
        indexes = []
        for index_class in cls.__indexes__:
            indexes.append(
                f'::{index_class.__index_name__}::{index_class.__key__}'
            )
        with redis.pipeline(transaction=True) as pipe:
            for member in members:
                is_index = False
                for index in indexes:
                    if index in member:
                        is_index = True
                        break
                if not is_index:
                    pipe.hgetall(member)
            result_data = pipe.execute()

        result = []
        for data in result_data:
            result.append(cls(**data))
        return result

    def delete(self, redis: Union[Pipeline, Redis]):
        if isinstance(redis, Pipeline):
            pipe = redis
        else:
            pipe = redis.pipeline()

        for index_class in self.__indexes__:
            if getattr(self, index_class.__key__) is not None:
                index_class.remove(pipe, self)

        pipe.delete(self.redis_key)
        if not isinstance(redis, Pipeline):
            pipe.execute()

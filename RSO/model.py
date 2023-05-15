from typing import Union

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
    def search(cls, redis: Redis, value):
        redis_key = cls.redis_key_from_value(value)
        if bool(redis.exists(redis_key)):
            fields = cls.get_fields()
            redis_data = redis.hmget(redis_key, fields)
            dict_data = cls.from_redis(dict(zip(fields, redis_data)))
            return cls(**dict_data)
        else:
            return None

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

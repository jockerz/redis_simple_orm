from typing import Union

from redis.client import Pipeline, Redis

from RSO.base import BaseModel


class Model(BaseModel):
	class Config:
		orm_mode = True

	def is_exists(self, redis: Redis):
		return bool(redis.exists(self.redis_key))

	def to_redis(self):
		return self.dict()

	def save(self, redis: Union[Pipeline, Redis]):
		if isinstance(redis, Pipeline):
			pipe = redis
		else:
			pipe = redis.pipeline()

		pipe.hmset(self.redis_key, self.to_redis())
		for index_class in self.__indexes__:
			index = index_class.create_from_model(self)
			index.save_index(pipe)
		pipe.execute()

	@classmethod
	def search(cls, redis: Redis, value):
		redis_key = cls._to_redis_key(value)
		if bool(redis.exists(redis_key)):
			redis_data = redis.hgetall(redis_key)
			return cls(**redis_data)
		else:
			return None

	def delete(self, redis: [Pipeline, Redis]):
		if isinstance(redis, Pipeline):
			pipe = redis
		else:
			pipe = redis.pipeline()

		for index_class in self.__indexes__:
			index = index_class.create_from_model(self)
			index.remove_from_index(pipe)

		pipe.delete(self.redis_key)
		pipe.execute()

		del self

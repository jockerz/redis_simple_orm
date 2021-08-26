from typing import List

from pydantic import BaseModel as PydanticBaseModel

REDIS_MODEL_PREFIX = 'simple_redis_orm'


class BaseIndex:
    # prefix for redis key
    __prefix__: str = REDIS_MODEL_PREFIX
    __index_name__: str = 'index_base'
    # Model class that using this index
    __model__: 'BaseModel'
    __key__: str

    @property
    def _model_key_value(self):
        return getattr(self.__model__, self.__model__.__key__)

    @classmethod
    def create_from_model(cls, model_instance: 'BaseModel'):
        cls.__model__ = model_instance
        return cls()


class BaseModel:
    # prefix for redis key
    __prefix__: str = REDIS_MODEL_PREFIX
    # infix for redis key and model name
    __model_name__: str
    # Object property name that are to be redis key suffix
    __key__: str
    __indexes__: List[BaseIndex] = None

    @classmethod
    def _to_redis_key(cls, value):
        return f'{cls.__prefix__}::{cls.__model_name__}:{value}'

    @property
    def redis_key(self):
        return self._to_redis_key(getattr(self, self.__key__))

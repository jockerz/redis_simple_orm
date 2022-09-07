from datetime import date, datetime
from dataclasses import asdict
from typing import List, Type, TypeVar


T = TypeVar('T')


REDIS_MODEL_PREFIX = 'simple_redis_orm'


class BaseIndex:
    # prefix for redis key
    __prefix__: str = REDIS_MODEL_PREFIX
    __index_name__: str = 'index_base'
    # Model class that using this index
    __model__: T
    __key__: str

    @property
    def _model_key_value(self):
        return getattr(self.__model__, self.__model__.__key__)

    @classmethod
    def create_from_model_class(cls, model_instance: Type["BaseModel"]):
        cls.__model__ = model_instance
        return cls()


class BaseModel:
    # prefix for redis key
    __prefix__: str = REDIS_MODEL_PREFIX
    # infix for redis key and model name
    __model_name__: str
    # Object property name that are to be redis key suffix
    __key__: str
    __indexes__: List[BaseIndex] = []

    def __post_init__(self):
        for field, desc in self.__dataclass_fields__.items():
            f_value = getattr(self, field)
            if f_value is None:
                continue

            f_type = desc.type
            if f_type == bool and not isinstance(f_value, bool):
                # bool saved as 'True' / 'False' by txredisapi
                if f_value in ['False', '0']:
                    value = False
                else:
                    value = bool(f_value)
            elif f_type == date and not isinstance(f_value, date):
                value = date.fromisoformat(f_value)
            elif f_type == datetime and not isinstance(f_value, datetime):
                value = datetime.fromisoformat(f_value)
            else:
                continue
            setattr(self, field, value)

    @classmethod
    def _to_redis_key(cls, value):
        return f'{cls.__prefix__}::{cls.__model_name__}:{value}'

    @property
    def redis_key(self):
        return self._to_redis_key(getattr(self, self.__key__))

    def dict(self) -> dict:
        return asdict(self)

    def to_redis(self) -> dict:
        dict_data = self.dict()
        for key, value in dict_data.copy().items():
            if value is None:
                del dict_data[key]
        return dict_data

    @classmethod
    def from_redis(cls, dict_data: dict) -> dict:
        return dict_data

    @classmethod
    def search(cls, redis, value):
        raise NotImplementedError

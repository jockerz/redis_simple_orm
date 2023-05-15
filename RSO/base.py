from datetime import date, datetime
from dataclasses import asdict, fields
from enum import Enum
from typing import Any, ClassVar, List, TypeVar
from uuid import UUID

T = TypeVar('T')

REDIS_MODEL_PREFIX = None


class BaseIndex:
    # prefix for redis key
    __prefix__: str
    __index_name__: str = 'index'
    # Model class that using this index
    __model__: ClassVar
    __key__: str

    @classmethod
    def model_key_value(cls, model_obj: T) -> Any:
        value = getattr(model_obj, model_obj.__key__)
        if isinstance(value, UUID):
            value = str(value)
        return value

    @classmethod
    def index_key_value(cls, model_obj: T) -> Any:
        value = getattr(model_obj, cls.__key__)
        if isinstance(value, UUID):
            value = str(value)
        return value


class BaseHashIndex(BaseIndex):
    @classmethod
    def redis_key(cls) -> str:
        model_prefix = cls.__model__.__model_name__
        if cls.__prefix__ is not None:
            redis_key = f'{cls.__prefix__}::'
        else:
            redis_key = ''
        redis_key = f'{redis_key}{model_prefix}::' \
                    f'{cls.__index_name__}::{cls.__key__}'
        return redis_key


class BaseListIndex(BaseIndex):
    @classmethod
    def redis_key_from_value(cls, value: Any) -> str:
        model_prefix = cls.__model__.__model_name__
        if cls.__prefix__ is not None:
            redis_key = f'{cls.__prefix__}::'
        else:
            redis_key = ''
        redis_key = f'{redis_key}{model_prefix}::' \
                    f'{cls.__index_name__}::{cls.__key__}:{value}'
        return redis_key

    @classmethod
    def redis_key(cls, instance: T) -> str:
        value = getattr(instance, cls.__key__)
        return cls.redis_key_from_value(value)


class BaseSetIndex(BaseIndex):
    @classmethod
    def redis_key_from_value(cls, value: Any) -> str:
        model_prefix = cls.__model__.__model_name__
        if cls.__prefix__ is not None:
            redis_key = f'{cls.__prefix__}::'
        else:
            redis_key = ''
        redis_key = f'{redis_key}{model_prefix}::' \
                    f'{cls.__index_name__}::{cls.__key__}:{value}'
        return redis_key

    @classmethod
    def redis_key(cls, instance: T) -> str:
        value = getattr(instance, cls.__key__)
        return cls.redis_key_from_value(value)



class BaseModel:
    # prefix for redis key
    __prefix__: str
    # infix for redis key and model name
    __model_name__: str
    # Object property name that are to be redis key suffix
    __key__: str
    __indexes__: List[BaseIndex]

    @classmethod
    def get_fields(cls) -> List[str]:
        return [f.name for f in fields(cls)]

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
    def redis_key_from_value(cls, value):
        if isinstance(value, UUID):
            value = str(value)
        if cls.__prefix__ is None:
            return f'{cls.__model_name__}:{value}'
        return f'{cls.__prefix__}::{cls.__model_name__}:{value}'

    @property
    def redis_key(self):
        return self.redis_key_from_value(getattr(self, self.__key__))

    def dict(self) -> dict:
        return asdict(self)

    def to_redis(self):
        dict_data = self.dict()
        for key, value in self.dict().items():
            if value is None:
                del dict_data[key]
            elif isinstance(value, bool):
                dict_data[key] = int(value)
            elif isinstance(value, (date, datetime)):
                dict_data[key] = value.isoformat()
            elif isinstance(value, Enum):
                dict_data[key] = value.value
        return dict_data

    @classmethod
    def from_redis(cls, dict_data: dict) -> dict:
        return dict_data

    @classmethod
    def search(cls, redis, value):
        raise NotImplementedError

    @classmethod
    def all(cls, redis):
        raise NotImplementedError

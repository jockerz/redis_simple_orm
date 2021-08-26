from dataclasses import dataclass, field, InitVar
from datetime import date

from RSO.index import HashIndex, SetIndex
from RSO.model import Model
from RSO.aioredis.index import (
    HashIndex as AsyncHashIndex,
    SetIndex as AsyncSetIndex
)
from RSO.aioredis.model import Model as AsyncModel


REDIS_MODEL_PREFIX = 'MY_REDIS_MODEL'


class BaseIndexUsername:
    __prefix__ = REDIS_MODEL_PREFIX
    __model__ = 'IndexUsername'
    __key__ = 'username'


class BaseIndexEmail:
    __prefix__ = REDIS_MODEL_PREFIX
    __model__ = 'IndexEmail'
    __key__ = 'email'


class BaseIndexGroupID:
    __prefix__ = REDIS_MODEL_PREFIX
    __model__ = 'IndexGroupID'
    __key__ = 'group_id'


@dataclass
class BaseUserModel:
    __prefix__ = REDIS_MODEL_PREFIX
    __model_name__ = 'user'
    __key__ = 'user_id'

    user_id: int
    username: str
    email: str = field(default=None)
    group_id: int = field(default=None)
    birth_date: date = field(default=None)


# Sync


class SingleIndexUsername(BaseIndexUsername, HashIndex):
    pass


class SingleIndexEmail(BaseIndexEmail, HashIndex):
    pass


class SetIndexGroupID(BaseIndexGroupID, SetIndex):
    pass


@dataclass
class UserModel(Model, BaseUserModel):

    __indexes__ = [
        SingleIndexUsername,
        SingleIndexEmail,
        SetIndexGroupID
    ]

    def to_redis(self):
        dict_data = self.dict()
        if self.birth_date is not None:
            dict_data['birth_date'] = self.birth_date.isoformat()
        if self.email is None:
            del dict_data['email']
        return dict_data


# Async


class AsyncSingleIndexUsername(BaseIndexUsername, AsyncHashIndex):
    pass


class AsyncSingleIndexEmail(BaseIndexEmail, AsyncHashIndex):
    pass


class AsyncSetIndexGroupID(BaseIndexGroupID, AsyncSetIndex):
    pass


@dataclass
class AsyncUserModel(BaseUserModel, AsyncModel):

    __indexes__ = [
        AsyncSingleIndexUsername,
        AsyncSingleIndexEmail,
        AsyncSetIndexGroupID
    ]

    def to_redis(self):
        dict_data = self.dict()
        if self.birth_date is not None:
            dict_data['birth_date'] = self.birth_date.isoformat()
        return dict_data

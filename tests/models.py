from dataclasses import dataclass, field
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


class BaseUserModel:
    __prefix__ = REDIS_MODEL_PREFIX
    __model_name__ = 'user'
    __key__ = 'user_id'


# Sync


class SingleIndexUsername(BaseIndexUsername, HashIndex):
    pass


class SingleIndexEmail(BaseIndexEmail, HashIndex):
    pass


class SetIndexGroupID(BaseIndexGroupID, SetIndex):
    pass


class UserModel(Model, BaseUserModel):

    user_id: int
    username: str
    email: str = None
    group_id: int
    birth_date: date = None

    __indexes__ = [
        SingleIndexUsername,
        SingleIndexEmail,
        SetIndexGroupID
    ]

    def to_redis(self):
        dict_data = self.dict()
        if self.birth_date is not None:
            dict_data['birth_date'] = self.birth_date.isoformat()
        return dict_data


# Async


class AsyncSingleIndexUsername(BaseIndexUsername, AsyncHashIndex):
    pass


class AsyncSingleIndexEmail(BaseIndexEmail, AsyncHashIndex):
    pass


class AsyncSetIndexGroupID(BaseIndexGroupID, AsyncSetIndex):
    pass


class AsyncUserModel(BaseUserModel, AsyncModel):

    user_id: int
    username: str
    email: str = None
    group_id: int
    birth_date: date = None
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

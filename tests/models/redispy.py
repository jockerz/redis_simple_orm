from dataclasses import dataclass

from redis import Redis
from RSO.index import HashIndex, ListIndex, SetIndex
from RSO.model import Model

from .base import (
    BaseIndexGroupID,
    BaseIndexEmail,
    BaseIndexUsername,
    BaseIndexQueue,
    BaseUserModel
)


class SingleIndexUsername(BaseIndexUsername, HashIndex):
    pass


class SingleIndexEmail(BaseIndexEmail, HashIndex):
    pass


class SetIndexGroupID(BaseIndexGroupID, SetIndex):
    pass


class ListIndexQueue(BaseIndexQueue, ListIndex):
    pass


@dataclass
class UserModel(Model, BaseUserModel):
    __indexes__ = [
        SingleIndexUsername,
        SingleIndexEmail,
        SetIndexGroupID,
        ListIndexQueue
    ]

    def to_redis(self):
        dict_data = super(UserModel, self).to_redis()
        if self.birth_date is not None:
            dict_data['birth_date'] = self.birth_date.isoformat()
        if self.email is None:
            del dict_data['email']
        return dict_data

    @classmethod
    def search_by_queue(cls, redis: Redis, queue_id: int):
        return ListIndexQueue.search_models(redis, queue_id, cls)


class NoPrefixSingleIndexUsername(BaseIndexUsername, HashIndex):
    __prefix__ = None


class NoPrefixSingleIndexEmail(BaseIndexEmail, HashIndex):
    __prefix__ = None


class NoPrefixSetIndexGroupID(BaseIndexGroupID, SetIndex):
    __prefix__ = None


class NoPrefixListIndexQueue(BaseIndexQueue, ListIndex):
    __prefix__ = None


@dataclass
class NoPrefixUserModel(Model, BaseUserModel):
    __prefix__ = None

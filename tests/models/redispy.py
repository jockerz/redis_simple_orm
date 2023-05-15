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


@dataclass
class UserModel(Model, BaseUserModel):
    @classmethod
    def search_by_queue(cls, redis: Redis, queue_id: int):
        return ListIndexQueue.search_models(redis, queue_id)


class SingleIndexUsername(BaseIndexUsername, HashIndex):
    __model__ = UserModel


class SingleIndexEmail(BaseIndexEmail, HashIndex):
    __model__ = UserModel


class SetIndexGroupID(BaseIndexGroupID, SetIndex):
    __model__ = UserModel


class ListIndexQueue(BaseIndexQueue, ListIndex):
    __model__ = UserModel


UserModel.__indexes__ = [
    SingleIndexUsername,
    SingleIndexEmail,
    SetIndexGroupID,
    ListIndexQueue
]


@dataclass
class NoPrefixUserModel(Model, BaseUserModel):
    __prefix__ = None


class NoPrefixSingleIndexUsername(BaseIndexUsername, HashIndex):
    __prefix__ = None
    __model__ = NoPrefixUserModel


class NoPrefixSingleIndexEmail(BaseIndexEmail, HashIndex):
    __prefix__ = None
    __model__ = NoPrefixUserModel


class NoPrefixSetIndexGroupID(BaseIndexGroupID, SetIndex):
    __prefix__ = None
    __model__ = NoPrefixUserModel


class NoPrefixListIndexQueue(BaseIndexQueue, ListIndex):
    __prefix__ = None
    __model__ = NoPrefixUserModel


NoPrefixUserModel.__indexes__ = [
    NoPrefixSingleIndexUsername,
    NoPrefixSingleIndexEmail,
    NoPrefixSetIndexGroupID,
    NoPrefixListIndexQueue
]

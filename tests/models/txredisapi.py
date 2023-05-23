from dataclasses import dataclass
from typing import Union

from twisted.internet import defer
from txredisapi import BaseRedisProtocol, ConnectionHandler

from RSO.txredisapi.index import HashIndex, ListIndex, SetIndex
from RSO.txredisapi.model import Model

from .base import (
    BaseIndexEmail,
    BaseIndexGroupID,
    BaseIndexQueue,
    BaseIndexUsername,
    BaseUserModel,
)


@dataclass
class UserModel(BaseUserModel, Model):
    @classmethod
    @defer.inlineCallbacks
    def search_by_queue(
        cls, redis: ConnectionHandler, queue_id: int
    ):
        res = yield ListIndexQueue.search_models(redis, queue_id)
        return res

    @classmethod
    @defer.inlineCallbacks
    def search_by_list_rpushlpop(
        cls, redis: ConnectionHandler, queue_id: int
    ):
        """Search for model and do `rpushlpop` on the index"""
        res = yield ListIndexQueue.get_by_rpoplpush(redis, queue_id)
        return res


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

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


class SingleIndexUsername(BaseIndexUsername, HashIndex):
    pass


class SingleIndexEmail(BaseIndexEmail, HashIndex):
    pass


class SetIndexGroupID(BaseIndexGroupID, SetIndex):
    pass


class ListIndexQueue(BaseIndexQueue, ListIndex):
    pass


@dataclass
class UserModel(BaseUserModel, Model):
    __indexes__ = [
        SingleIndexUsername,
        SingleIndexEmail,
        SetIndexGroupID,
        ListIndexQueue
    ]

    @classmethod
    @defer.inlineCallbacks
    def search_by_queue(
        cls, redis: ConnectionHandler, queue_id: int
    ):
        res = yield ListIndexQueue.search_models(redis, queue_id, cls)
        return res

    @classmethod
    @defer.inlineCallbacks
    def search_by_list_rpushlpop(
        cls, redis: ConnectionHandler, queue_id: int
    ):
        """Search for model and do `rpushlpop` on the index"""
        res = yield ListIndexQueue.get_by_rpoplpush(redis, queue_id, cls)
        return res


class ExtendedUserModel(UserModel):

    @defer.inlineCallbacks
    def save(self, redis: Union[BaseRedisProtocol, ConnectionHandler]):
        yield super(ExtendedUserModel, self).extended_save(redis)


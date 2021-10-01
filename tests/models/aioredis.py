from dataclasses import dataclass
from typing import Union

try:
    from aioredis.client import Redis, Pipeline
except ModuleNotFoundError:
    from aioredis.commands import Redis, Pipeline
from RSO.aioredis.index import HashIndex, ListIndex, SetIndex
from RSO.aioredis.model import Model

from .base import (
    BaseIndexEmail,
    BaseIndexGroupID,
    BaseIndexQueue,
    BaseIndexUsername,
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
class UserModel(BaseUserModel, Model):
    __indexes__ = [
        SingleIndexUsername,
        SingleIndexEmail,
        SetIndexGroupID,
        ListIndexQueue
    ]

    @classmethod
    async def search_by_queue(cls, redis, queue_id: int):
        return await ListIndexQueue.search_models(redis, queue_id, cls)

    @classmethod
    async def search_by_list_rpushlpop(cls, redis, queue_id: int):
        return await ListIndexQueue.get_by_rpoplpush(redis, queue_id, cls)


class ExtendedUserModel(UserModel):

    async def save(self, redis: Union[Pipeline, Redis]):
        return await super(ExtendedUserModel, self).extended_save(redis)

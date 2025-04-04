import typing as t
from dataclasses import dataclass

from redis.asyncio.client import Redis, Pipeline
from RSO.asyncio.index import HashIndex, ListIndex, SetIndex
from RSO.asyncio.model import Model

from .base import (
    BaseIndexEmail,
    BaseIndexGroupID,
    BaseIndexQueue,
    BaseIndexUsername,
    BaseUserModel
)


@dataclass
class UserModel(BaseUserModel, Model):
    @classmethod
    async def search_by_email(
        cls, redis: Redis, email: str
    ) -> t.Optional["UserModel"]:
        return await SingleIndexEmail.search_model(redis, email)

    @classmethod
    async def search_by_username(
        cls, redis: Redis, username: str
    ) -> t.Optional["UserModel"]:
        return await SingleIndexUsername.search_model(redis, username)

    @classmethod
    async def search_by_queue(cls, redis, queue_id: int) -> t.List["UserModel"]:
        return await ListIndexQueue.search_models(redis, queue_id)

    @classmethod
    async def search_by_list_rpushlpop(
        cls, redis, queue_id: int
    ) -> t.List["UserModel"]:
        return await ListIndexQueue.get_by_rpoplpush(redis, queue_id)

    @classmethod
    async def search_by_group_id(
        cls, redis: Redis, group_id: int
    ) -> t.List["UserModel"]:
        return await SetIndexGroupID.search_models(redis, group_id)


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


# TODO
class ExtendedUserModel(UserModel):
    async def save(self, redis: t.Union[Pipeline, Redis]) -> None:
        return await super(ExtendedUserModel, self).extended_save(redis)

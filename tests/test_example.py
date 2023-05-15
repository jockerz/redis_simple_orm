from dataclasses import dataclass, field

import pytest
from fakeredis import FakeRedis as Redis, aioredis

from RSO.index import HashIndex, SetIndex
from RSO.model import Model
from RSO.asyncio.index import (
    HashIndex as AsyncHashIndex,
    SetIndex as AsyncSetIndex
)
from RSO.asyncio.model import Model as AsyncModel

from tests.models.base import BaseUserModel
from tests.models.const import REDIS_MODEL_PREFIX
from .data import USERS


@dataclass
class UserModel(Model, BaseUserModel):
    __prefix__ = REDIS_MODEL_PREFIX
    __model_name__ = 'user'
    __key__ = 'user_id'

    """For easier access, we create some searching method"""

    @classmethod
    def search_by_username(cls, redis: Redis, username: str):
        return SingleIndexUsername.search_model(redis, username)

    @classmethod
    def search_by_email(cls, redis: Redis, email: str):
        return SingleIndexEmail.search_model(redis, email)

    @classmethod
    def search_group_member(cls, redis: Redis, group_id: int):
        return SetIndexGroupID.search_models(redis, group_id)


class SingleIndexUsername(HashIndex):
    __prefix__ = REDIS_MODEL_PREFIX
    __model__ = UserModel
    __key__ = 'username'


class SingleIndexEmail(HashIndex):
    __prefix__ = REDIS_MODEL_PREFIX
    __model__ = UserModel
    __key__ = 'email'


class SetIndexGroupID(SetIndex):
    __prefix__ = REDIS_MODEL_PREFIX
    __model__ = UserModel
    __key__ = 'group_id'


UserModel.__indexes__ = [
    SingleIndexUsername,
    SingleIndexEmail,
    SetIndexGroupID
]


def test_main_sync(sync_redis):
    redis = sync_redis

    # save all user
    for user_data in USERS:
        user = UserModel(**user_data)
        print(f'{user.redis_key}: {user.dict()}')
        user.save(redis)

    """Now see how is the model and index data saved on redis :)"""
    print('redis keys:', redis.keys('*'))
    # search by id
    user = UserModel.search(redis, 1)
    assert user is not None

    # search by username
    user = UserModel.search_by_username(redis, 'first_user')
    assert user is not None
    user = UserModel.search_by_username(redis, 'not_exist')
    assert user is None

    # search by email
    user = UserModel.search_by_email(redis, 'first_user@contoh.com')
    assert user is not None
    user = UserModel.search_by_email(redis, 'not_exist@contoh.com')
    assert user is None

    # search by group id
    users = UserModel.search_group_member(redis, 1)
    assert len(users) == 3
    users = UserModel.search_group_member(redis, 2)
    assert len(users) == 2
    users = UserModel.search_group_member(redis, 1_000_000)
    assert len(users) == 0


# Async

@dataclass
class AsyncUserModel(AsyncModel, BaseUserModel):
    __prefix__ = REDIS_MODEL_PREFIX

    """For easier access, we create some searching method"""

    @classmethod
    async def search_by_username(cls, redis: Redis, username: str):
        return await AsyncSingleIndexUsername.search_model(redis, username)

    @classmethod
    async def search_by_email(cls, redis: Redis, email: str):
        return await AsyncSingleIndexEmail.search_model(redis, email)

    @classmethod
    async def search_group_member(cls, redis: Redis, group_id: int):
        return await AsyncSetIndexGroupID.search_models(redis, group_id)


class AsyncSingleIndexUsername(AsyncHashIndex):
    __prefix__ = REDIS_MODEL_PREFIX
    __model__ = AsyncUserModel
    __key__ = 'username'


class AsyncSingleIndexEmail(AsyncHashIndex):
    __prefix__ = REDIS_MODEL_PREFIX
    __model__ = AsyncUserModel
    __key__ = 'email'


class AsyncSetIndexGroupID(AsyncSetIndex):
    __prefix__ = REDIS_MODEL_PREFIX
    __model__ = AsyncUserModel
    __key__ = 'group_id'


AsyncUserModel.__indexes__ = [
    AsyncSingleIndexUsername,
    AsyncSingleIndexEmail,
    AsyncSetIndexGroupID
]


@pytest.mark.asyncio
async def test_async_main(async_redis):
    redis = async_redis

    # save all user
    for user_data in USERS:
        user = AsyncUserModel(**user_data)
        print(f'{user.redis_key}: {user.to_redis()}')
        await user.save(redis)

    """Now see how is the model and index data saved on redis :)"""

    # search by id
    user = await AsyncUserModel.search(redis, 1)
    assert user is not None

    # search by username
    user = await AsyncUserModel.search_by_username(redis, 'first_user')
    assert user is not None
    user = await AsyncUserModel.search_by_username(redis, 'not_exist')
    assert user is None

    # search by email
    user = await AsyncUserModel.search_by_email(redis, 'first_user@contoh.com')
    assert user is not None
    user = await AsyncUserModel.search_by_email(redis, 'not_exist@contoh.com')
    assert user is None

    # search by group id
    users = await AsyncUserModel.search_group_member(redis, 1)
    assert len(users) == 3
    users = await AsyncUserModel.search_group_member(redis, 2)
    assert len(users) == 2
    users = await AsyncUserModel.search_group_member(redis, 1_000_000)
    assert len(users) == 0

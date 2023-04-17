from datetime import date

import pytest

from ..models.aioredis import (
    UserModel,
    SingleIndexUsername,
    SingleIndexEmail,
    SetIndexGroupID
)


@pytest.mark.asyncio
class TestModelCreate:
    async def test_success(self, async_redis):
        user = UserModel(
            user_id=1,
            username='test_create_success',
            email='test@create.success',
            group_id=10,
            birth_date=date.fromisoformat('1999-09-09')
        )
        assert await user.is_exists(async_redis) is False

        await user.save(async_redis)
        assert await user.is_exists(async_redis) is True

        index_username = SingleIndexUsername.create_from_model_class(user)
        assert await async_redis.exists(index_username.redis_key)

        index_email = SingleIndexEmail.create_from_model_class(user)
        assert await async_redis.exists(index_email.redis_key)

        index_group_id = SetIndexGroupID.create_from_model_class(user)
        redis_key = index_group_id._to_redis_key(user.group_id)
        assert await async_redis.exists(redis_key)


@pytest.mark.asyncio
class TestModelCreate2:
    async def test_success(self, async_redis_2):
        async_redis = async_redis_2

        user = UserModel(
            user_id=1,
            username='test_create_success',
            email='test@create.success',
            group_id=10,
            birth_date=date.fromisoformat('1999-09-09')
        )
        assert await user.is_exists(async_redis) is False

        await user.save(async_redis)
        assert await user.is_exists(async_redis) is True

        index_username = SingleIndexUsername.create_from_model_class(user)
        assert await async_redis.exists(index_username.redis_key)

        index_email = SingleIndexEmail.create_from_model_class(user)
        assert await async_redis.exists(index_email.redis_key)

        index_group_id = SetIndexGroupID.create_from_model_class(user)
        redis_key = index_group_id._to_redis_key(user.group_id)
        assert await async_redis.exists(redis_key)


@pytest.mark.asyncio
class TestModelGet:
    async def test_success(self, async_redis):
        user = UserModel(
            user_id=1,
            username='test_create_success',
            email='test@create.success',
            group_id=10,
            birth_date=date.fromisoformat('1999-09-09')
        )
        await user.save(async_redis)
        assert await user.is_exists(async_redis) is True

        assert await UserModel.search(async_redis, user.user_id) \
               is not None

    async def test_not_found(self, async_redis):
        assert await UserModel.search(async_redis, 1) is None


@pytest.mark.asyncio
class TestModelGet2:
    async def test_success(self, async_redis_2):
        async_redis = async_redis_2

        user = UserModel(
            user_id=1,
            username='test_create_success',
            email='test@create.success',
            group_id=10,
            birth_date=date.fromisoformat('1999-09-09')
        )
        await user.save(async_redis)
        assert await user.is_exists(async_redis) is True

        assert await UserModel.search(async_redis, user.user_id) \
               is not None

    async def test_not_found(self, async_redis):
        assert await UserModel.search(async_redis, 1) is None


@pytest.mark.asyncio
class TestModelDelete:
    async def test_success(self, async_redis_2):
        async_redis = async_redis_2

        user = UserModel(
            user_id=1,
            username='test_create_success',
            email='test@create.success',
            group_id=10,
            birth_date=date.fromisoformat('1999-09-09')
        )
        await user.save(async_redis)
        assert await user.is_exists(async_redis) is True

        redis_key = user.redis_key

        assert await user.delete(async_redis) is None
        assert bool(await async_redis.exists(redis_key)) is False
        assert await async_redis.keys('*') == []


@pytest.mark.asyncio
class TestModelDelete2:
    async def test_success(self, async_redis):
        user = UserModel(
            user_id=1,
            username='test_create_success',
            email='test@create.success',
            group_id=10,
            birth_date=date.fromisoformat('1999-09-09')
        )
        await user.save(async_redis)
        assert await user.is_exists(async_redis) is True

        redis_key = user.redis_key

        assert await user.delete(async_redis) is None
        assert bool(await async_redis.exists(redis_key)) is False
        assert await async_redis.keys('*') == []

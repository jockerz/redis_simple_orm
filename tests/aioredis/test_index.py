from datetime import date

import pytest

from ..models.aioredis import (
    UserModel,
    ExtendedUserModel,
    ListIndexQueue,
)


@pytest.mark.asyncio
class TestListIndex:
    async def test_has_list_index(self, async_redis):
        user = UserModel(
            user_id=1,
            username='test_create_success',
            queue_id=3,
            birth_date=date.fromisoformat('1999-09-09')
        )
        await user.save(async_redis)

        index = ListIndexQueue.create_from_model(user)

        res = await index.is_exist_on_list(async_redis, user.user_id)
        assert res is not None

        user_id_list = await async_redis.lrange(index.redis_key, 0, -1)
        assert user_id_list.count(str(user.user_id)) == 1

    async def test_save_multiple_time(self, async_redis):
        user = UserModel(
            user_id=1,
            username='test_create_success',
            queue_id=3,
            birth_date=date.fromisoformat('1999-09-09')
        )
        await user.save(async_redis)

        index = ListIndexQueue.create_from_model(user)
        assert (await index.is_exist_on_list(async_redis, user.user_id)) \
               is True

        await user.save(async_redis)

        user_id_list = await async_redis.lrange(index.redis_key, 0, -1)
        assert user_id_list.count(str(user.user_id)) == 2

    async def test_using_extended_save_multiple_times(self, async_redis):
        user = ExtendedUserModel(
            user_id=1,
            username='test_create_success',
            email='test@create.success',
            group_id=2,
            queue_id=3,
            birth_date=date.fromisoformat('1999-09-09')
        )
        await user.save(async_redis)
        await user.save(async_redis)

        index = ListIndexQueue.create_from_model(user)
        user_id_list = await async_redis.lrange(index.redis_key, 0, -1)
        assert user_id_list.count(str(user.user_id)) == 1

    async def test_not_use_list_index(self, async_redis):
        user = ExtendedUserModel(
            user_id=1,
            username='test_create_success',
        )
        await user.save(async_redis)

        index = ListIndexQueue.create_from_model(user)

        user_id_list = await async_redis.lrange(index.redis_key, 0, -1)
        assert user_id_list.count(str(user.user_id)) == 0

        assert (await index.is_exist_on_list(async_redis, user.user_id)) \
               is False

    async def test_rpushlpop(self, async_redis):
        for data in (
            dict(user_id=1, username='uname1', queue_id=3,),
            dict(user_id=2, username='uname2', queue_id=3,),
        ):
            user = ExtendedUserModel(**data)
            await user.save(async_redis)

        index = ListIndexQueue.create_from_model(user)
        old_list_data = await async_redis.lrange(index.redis_key, 0, -1)
        assert len(old_list_data) == 2

        user = await ExtendedUserModel.search_by_list_rpushlpop(
            async_redis, queue_id=3
        )

        assert isinstance(user, ExtendedUserModel)
        new_list_data = await async_redis.lrange(index.redis_key, 0, -1)
        assert len(new_list_data) == 2

        assert new_list_data[0] == old_list_data[1]
        assert new_list_data[1] == old_list_data[0]

    async def test_model_delete(self, async_redis):
        user = ExtendedUserModel(
            user_id=1, username='username', queue_id=3,
        )
        await user.save(async_redis)
        await user.save(async_redis)

        index = ListIndexQueue.create_from_model(user)
        assert (await index.is_exist_on_list(async_redis, user.user_id)) \
               is True

        users = await ListIndexQueue.search_models(
            async_redis, index_value=3, model_class=ExtendedUserModel
        )
        assert len(users) == 1

        # delete user
        await user.delete(async_redis)

        assert (await index.is_exist_on_list(async_redis, user.user_id)) \
               is False

        users = await ListIndexQueue.search_models(
            async_redis, index_value=3, model_class=ExtendedUserModel
        )
        assert len(users) == 0

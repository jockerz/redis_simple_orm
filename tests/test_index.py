from datetime import date

from tests.models.const import REDIS_MODEL_PREFIX
from .models.redispy import (
    UserModel,
    SingleIndexEmail,
    SingleIndexUsername,
    SetIndexGroupID,
    ListIndexQueue,
    NoPrefixUserModel,
    NoPrefixSingleIndexUsername,
    NoPrefixSetIndexGroupID,
    NoPrefixListIndexQueue,
)

BIRTH_DATE = date.fromisoformat('1999-09-09')


class TestHashIndex:
    def test_redis_key(self):
        # With prefix
        assert SingleIndexUsername.redis_key().startswith(REDIS_MODEL_PREFIX), \
            f'redis_key: {SingleIndexUsername.redis_key()}'

        # Without prefix
        assert not NoPrefixSingleIndexUsername.redis_key().startswith(
            REDIS_MODEL_PREFIX
        ), f'redis_key: {NoPrefixSingleIndexUsername.redis_key()}'


    def test_search_model(self, sync_redis):
        user = UserModel(user_id=1, username='username', email='test@email')
        user.save(sync_redis)

        assert SingleIndexUsername.search_model(sync_redis, user.username) \
               is not None
        assert SingleIndexEmail.search_model(sync_redis, user.email) \
               is not None

    def test_search_not_found(self, sync_redis):
        assert SingleIndexUsername.search_model(sync_redis, 'not_exist') \
               is None

        assert SingleIndexEmail.search_model(sync_redis, 'not_exist@email') \
               is None

    def test_after_delete(self, sync_redis):
        user = UserModel(
            user_id=1, username='username', email='test@email'
        )
        user.save(sync_redis)

        assert SingleIndexUsername.search_model(sync_redis, user.username) \
               is not None
        assert SingleIndexEmail.search_model(sync_redis, user.email) \
               is not None

        user.delete(sync_redis)

        assert SingleIndexUsername.search_model(sync_redis, user.username) \
               is None
        assert SingleIndexEmail.search_model(sync_redis, user.email) \
               is None


class TestListIndex:
    def test_redis_key(self):
        # With prefix
        user = UserModel(
            user_id=1, username='username', email='test@email'
        )
        assert ListIndexQueue.redis_key(user).startswith(REDIS_MODEL_PREFIX)

        # Without prefix
        user = NoPrefixUserModel(
            user_id=1, username='username', email='test@email'
        )
        assert not NoPrefixListIndexQueue.redis_key(user).startswith(
            REDIS_MODEL_PREFIX
        )


    def test_success(self, sync_redis):
        user = UserModel(
            user_id=1,
            username='test_create_success',
            email='test@create.success',
            group_id=2,
            queue_id=3,
            birth_date=BIRTH_DATE
        )
        user.save(sync_redis)

        assert ListIndexQueue.has_member_value(
            sync_redis, user.queue_id, user.user_id
        ) is True
        assert ListIndexQueue.has_member(sync_redis, user) is True
        assert sync_redis.exists(ListIndexQueue.redis_key(user))
        assert len(
            ListIndexQueue.get_members(sync_redis, user.queue_id)
        ) == 1

    def test_multiple_times_saved(self, sync_redis):
        user = UserModel(
            user_id=1,
            username='test_create_success',
            email='test@create.success',
            group_id=2,
            queue_id=3,
            birth_date=date.fromisoformat('1999-09-09')
        )
        user.save(sync_redis)

        assert ListIndexQueue.has_member(sync_redis, user) is True

        user.save(sync_redis)
        assert len(sync_redis.lrange(
            ListIndexQueue.redis_key(user), 0, -1
        )) == 2

    def test_not_using_list_index(self, sync_redis):
        user = UserModel(
            user_id=1,
            username='test_create_success',
            email='test@create.success',
            group_id=2,
            birth_date=date.fromisoformat('1999-09-09')
        )
        user.save(sync_redis)

        assert ListIndexQueue.has_member(sync_redis, user) is False

    def test_rpushlpop(self, sync_redis):
        for data in (
            dict(user_id=1, username='uname1', queue_id=3, email='test1@email'),
            dict(user_id=2, username='uname2', queue_id=3, email='test2@email'),
        ):
            user = UserModel(**data)
            user.save(sync_redis)

        redis_key = ListIndexQueue.redis_key_from_value(user.queue_id)
        old_list_data = sync_redis.lrange(redis_key, 0, -1)

        user = ListIndexQueue.get_by_rpoplpush(sync_redis, 3)
        assert user is not None

        new_list_data = sync_redis.lrange(redis_key, 0, -1)
        assert len(new_list_data) == 2
        assert new_list_data[0] == old_list_data[1]
        assert new_list_data[1] == old_list_data[0]

    def test_after_delete(self, sync_redis):
        user = UserModel(
            user_id=1,
            username='test_create_success',
            email='test@email',
            group_id=2,
            queue_id=3,
            birth_date=date.fromisoformat('1999-09-09')
        )
        user.save(sync_redis)
        user.delete(sync_redis)

        assert ListIndexQueue.has_member_value(
            sync_redis, user.queue_id, user.user_id
        ) is False
        assert len(ListIndexQueue.search_models(sync_redis, user.queue_id)) \
               == 0


class TestSetIndex:

    def test_redis_key(self):
        # With prefix
        user = UserModel(
            user_id=1, username='username', email='test@email'
        )
        assert SetIndexGroupID.redis_key(user).startswith(REDIS_MODEL_PREFIX)

        # Without prefix
        user = NoPrefixUserModel(
            user_id=1, username='username', email='test@email'
        )
        assert not NoPrefixSetIndexGroupID.redis_key(user).startswith(
            REDIS_MODEL_PREFIX
        )

    def test_search_model(self, sync_redis):
        user = UserModel(
            user_id=1, username='username', group_id=10,
            email='test@email',
        )
        user.save(sync_redis)

        result = SetIndexGroupID.search_models(sync_redis, 10)
        assert len(result) == 1

    def test_after_delete(self, sync_redis):
        user = UserModel(
            user_id=1, username='username', group_id=10,
            email='test@email',
        )
        user.save(sync_redis)
        user.delete(sync_redis)

        assert len(SetIndexGroupID.search_models(sync_redis, 10,)) == 0

    def test_not_found(self, sync_redis):
        assert len(SetIndexGroupID.search_models(sync_redis, 10)) == 0

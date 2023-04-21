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
        user = UserModel(
            user_id=1, username='username', email='test@email'
        )
        index = SingleIndexUsername.create_from_model_class(user)
        assert index.redis_key.startswith(REDIS_MODEL_PREFIX)

        # Without prefix
        user = NoPrefixUserModel(
            user_id=1, username='username', email='test@email'
        )
        index = NoPrefixSingleIndexUsername.create_from_model_class(user)
        assert not index.redis_key.startswith(REDIS_MODEL_PREFIX)


    def test_search_model(self, sync_redis):
        user = UserModel(
            user_id=1, username='username', email='test@email'
        )
        user.save(sync_redis)

        assert SingleIndexUsername.search_model(
            sync_redis, user.username, UserModel
        ) is not None
        assert SingleIndexEmail.search_model(
            sync_redis, user.email, UserModel
        ) is not None

    def test_search_not_found(self, sync_redis):
        assert SingleIndexUsername.search_model(
            sync_redis, 'not_exist', UserModel
        ) is None

        assert SingleIndexEmail.search_model(
            sync_redis, 'not_exist@email', UserModel
        ) is None

    def test_after_delete(self, sync_redis):
        user = UserModel(
            user_id=1, username='username', email='test@email'
        )
        user.save(sync_redis)

        assert SingleIndexUsername.search_model(
            sync_redis, user.username, UserModel
        ) is not None
        assert SingleIndexEmail.search_model(
            sync_redis, user.email, UserModel
        ) is not None

        user.delete(sync_redis)

        assert SingleIndexUsername.search_model(
            sync_redis, user.username, UserModel
        ) is None
        assert SingleIndexEmail.search_model(
            sync_redis, user.email, UserModel
        ) is None


class TestListIndex:
    def test_redis_key(self):
        # With prefix
        user = UserModel(
            user_id=1, username='username', email='test@email'
        )
        index = ListIndexQueue.create_from_model_class(user)
        assert index.redis_key.startswith(REDIS_MODEL_PREFIX)

        # Without prefix
        user = NoPrefixUserModel(
            user_id=1, username='username', email='test@email'
        )
        index = NoPrefixListIndexQueue.create_from_model_class(user)
        assert not index.redis_key.startswith(REDIS_MODEL_PREFIX)


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

        index = ListIndexQueue.create_from_model_class(user)

        assert index.is_exist_on_list(sync_redis, user.user_id) is True
        assert sync_redis.exists(index.redis_key)
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

        index = ListIndexQueue.create_from_model_class(user)
        assert index.is_exist_on_list(sync_redis, user.user_id) is True

        user.save(sync_redis)
        assert len(sync_redis.lrange(index.redis_key, 0, -1)) == 2

    def test_not_using_list_index(self, sync_redis):
        user = UserModel(
            user_id=1,
            username='test_create_success',
            email='test@create.success',
            group_id=2,
            birth_date=date.fromisoformat('1999-09-09')
        )
        user.save(sync_redis)
        index = ListIndexQueue.create_from_model_class(user)

        assert len(sync_redis.lrange(index.redis_key, 0, -1)) == 0
        assert index.is_exist_on_list(sync_redis, user.user_id) is False

    def test_rpushlpop(self, sync_redis):
        for data in (
            dict(user_id=1, username='uname1', queue_id=3, email='test1@email'),
            dict(user_id=2, username='uname2', queue_id=3, email='test2@email'),
        ):
            user = UserModel(**data)
            user.save(sync_redis)

        index = ListIndexQueue.create_from_model_class(user)

        old_list_data = sync_redis.lrange(index.redis_key, 0, -1)

        redis_key = index.redis_key
        user = ListIndexQueue.get_by_rpoplpush(sync_redis, 3, UserModel)
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
        index = ListIndexQueue.create_from_model_class(user)
        user.delete(sync_redis)

        assert index.is_exist_on_list(sync_redis, user.user_id) is False
        assert len(ListIndexQueue.search_models(
            sync_redis, user.queue_id, UserModel
        )) == 0


class TestSetIndex:

    def test_redis_key(self):
        # With prefix
        user = UserModel(
            user_id=1, username='username', email='test@email'
        )
        index = SetIndexGroupID.create_from_model_class(user)
        assert index.redis_key.startswith(REDIS_MODEL_PREFIX)

        # Without prefix
        user = NoPrefixUserModel(
            user_id=1, username='username', email='test@email'
        )
        index = NoPrefixSetIndexGroupID.create_from_model_class(user)
        assert not index.redis_key.startswith(REDIS_MODEL_PREFIX)

    def test_search_model(self, sync_redis):
        user = UserModel(
            user_id=1, username='username', group_id=10,
            email='test@email',
        )
        user.save(sync_redis)

        result = SetIndexGroupID.search_models(sync_redis, 10, UserModel)
        assert len(result) == 1

    def test_after_delete(self, sync_redis):
        user = UserModel(
            user_id=1, username='username', group_id=10,
            email='test@email',
        )
        user.save(sync_redis)
        user.delete(sync_redis)

        assert len(SetIndexGroupID.search_models(
            sync_redis, 10, UserModel
        )) == 0

    def test_not_found(self, sync_redis):
        assert len(SetIndexGroupID.search_models(
            sync_redis, 10, UserModel
        )) == 0

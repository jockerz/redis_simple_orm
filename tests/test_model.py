from datetime import date

from tests.models.const import REDIS_MODEL_PREFIX
from .models.redispy import (
    UserModel,
    SingleIndexUsername,
    SingleIndexEmail,
    SetIndexGroupID,
    NoPrefixUserModel
)


class TestModelCreate:
    def test_redis_key(self):
        # With prefix
        user = UserModel(
            user_id=1, username='test', email='test@create.success',
            group_id=10, birth_date=date.fromisoformat('1999-09-09')
        )
        assert user.redis_key.startswith(REDIS_MODEL_PREFIX), \
            f'key={user.redis_key} prefix={UserModel.__prefix__} ' \
            f'REDIS_MODEL_PREFIX={REDIS_MODEL_PREFIX}'

        # Without prefix
        user2 = NoPrefixUserModel(
            user_id=1, username='test', email='test@create.success',
            group_id=10, birth_date=date.fromisoformat('1999-09-09')
        )
        assert not user2.redis_key.startswith(REDIS_MODEL_PREFIX), \
            f'key={user2.redis_key} prefix={UserModel.__prefix__} ' \
            f'REDIS_MODEL_PREFIX={REDIS_MODEL_PREFIX}'

    def test_success(self, sync_redis):
        user = UserModel(
            user_id=1,
            username='test_create_success',
            email='test@create.success',
            group_id=10,
            birth_date=date.fromisoformat('1999-09-09')
        )
        assert user.is_exists(sync_redis) is False

        user.save(sync_redis)
        assert user.is_exists(sync_redis) is True

        assert bool(sync_redis.exists(SingleIndexUsername.redis_key())) \
               is True
        assert bool(sync_redis.exists(SingleIndexUsername.redis_key())) is True

    def test_double_save(self, sync_redis):
        user = UserModel(
            user_id=1,
            username='test_create_success',
            email='test@create.success',
            group_id=10,
            birth_date=date.fromisoformat('1999-09-09')
        )
        user.save(sync_redis)
        user.save(sync_redis)

        assert user.is_exists(sync_redis) is True
        assert SingleIndexUsername.search_model(sync_redis, user.username) \
               is not None
        assert SingleIndexEmail.search_model(sync_redis, user.email) \
               is not None
        assert len(SetIndexGroupID.search_models(sync_redis, user.group_id)) \
               == 1

class TestModelGet:
    def test_success(self, sync_redis):
        user = UserModel(
            user_id=1,
            username='test_create_success',
            email='test@create.success',
            group_id=10,
            birth_date=date.fromisoformat('1999-09-09')
        )
        user.save(sync_redis)
        assert user.is_exists(sync_redis) is True

        assert UserModel.search(sync_redis, user.user_id) \
               is not None

    def test_not_found(self, sync_redis):
        assert UserModel.search(sync_redis, 1) is None


class TestModelDelete:
    def test_success(self, sync_redis):
        user = UserModel(
            user_id=1,
            username='test_create_success',
            email='test@create.success',
            group_id=10,
            birth_date=date.fromisoformat('1999-09-09')
        )
        user.save(sync_redis)
        assert user.is_exists(sync_redis) is True

        redis_key = user.redis_key

        assert user.delete(sync_redis) is None
        assert bool(sync_redis.exists(redis_key)) is False
        assert sync_redis.keys('*') == []

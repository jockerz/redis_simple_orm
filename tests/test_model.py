from datetime import date

from .models.redispy import (
    UserModel,
    SingleIndexUsername,
    SingleIndexEmail,
    SetIndexGroupID
)


class TestModelCreate:
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

        index_username = SingleIndexUsername.create_from_model(user)
        assert bool(sync_redis.exists(index_username.redis_key)) \
               is True

        index_email = SingleIndexEmail.create_from_model(user)
        assert bool(sync_redis.exists(index_email.redis_key)) is True

        index_group_id = SetIndexGroupID.create_from_model(user)
        redis_key = index_group_id._to_redis_key(user.group_id)
        assert bool(sync_redis.exists(redis_key)) is True


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

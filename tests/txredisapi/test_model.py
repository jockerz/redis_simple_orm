from datetime import date

import pytest_twisted

from ..models.txredisapi import (
    UserModel,
    ListIndexQueue,
    SingleIndexUsername,
    SingleIndexEmail,
    SetIndexGroupID,
)


class TestModelCreate:
    @pytest_twisted.inlineCallbacks
    def test_complete(self, tx_redis):
        user = UserModel(
            user_id=1,
            username='test_create_success',
            email='test@create.success',
            group_id=2,
            queue_id=3,
            birth_date=date.fromisoformat('1999-09-09')
        )

        res = yield user.is_exist(tx_redis)
        assert res is False

        yield user.save(tx_redis)
        res = yield user.is_exist(tx_redis)
        assert res is True

        index_username = SingleIndexUsername.create_from_model(user)
        res = yield tx_redis.exists(index_username.redis_key)
        assert bool(res) is True

        index_email = SingleIndexEmail.create_from_model(user)
        res = yield tx_redis.exists(index_email.redis_key)
        assert bool(res) is True

        index_group_id = SetIndexGroupID.create_from_model(user)
        res = yield tx_redis.exists(index_group_id.redis_key)
        assert bool(res) is True

        index_queue = ListIndexQueue.create_from_model(user)
        res = yield tx_redis.exists(index_queue.redis_key)
        assert bool(res) is True


class TestModelGet:
    @pytest_twisted.inlineCallbacks
    def test_success(self, tx_redis):
        user = UserModel(
            user_id=1,
            username='test_create_success',
            email='test@create.success',
            group_id=2,
            queue_id=3,
            birth_date=date.fromisoformat('1999-09-09')
        )
        yield user.save(tx_redis)

        res = yield UserModel.search(tx_redis, 1)
        assert isinstance(res, UserModel)

    @pytest_twisted.inlineCallbacks
    def test_not_found(self, tx_redis):
        res = yield UserModel.search(tx_redis, 1)
        assert res is None


class TestModelDelete:

    @pytest_twisted.inlineCallbacks
    def test_success(self, tx_redis):
        user = UserModel(
            user_id=1,
            username='test_create_success',
            email='test@create.success',
            group_id=2,
            queue_id=3,
            birth_date=date.fromisoformat('1999-09-09')
        )
        redis_key = user.redis_key

        yield user.save(tx_redis)
        res = yield user.is_exist(tx_redis)
        assert res is True
        res = yield tx_redis.exists(redis_key)
        yield bool(res) is True

        yield user.delete(tx_redis)
        res = yield tx_redis.exists(redis_key)
        yield bool(res) is False

    @pytest_twisted.inlineCallbacks
    def test_index_removed(self, tx_redis):
        user = UserModel(
            user_id=1,
            username='test_create_success',
            email='test@create.success',
            group_id=2,
            queue_id=3,
            birth_date=date.fromisoformat('1999-09-09')
        )
        yield user.save(tx_redis)

        index_keys = []
        for index_class in UserModel.__indexes__ or []:
            if getattr(user, index_class.__key__) is None:
                continue
            index = index_class.create_from_model(user)
            index_keys.append(index.redis_key)
            res = yield tx_redis.exists(index.redis_key)
            assert bool(res) is True

        yield user.delete(tx_redis)
        for key in index_keys:
            res = yield tx_redis.exists(key)
            assert bool(res) is False

    @pytest_twisted.inlineCallbacks
    def test_not_found(self, tx_redis):
        user = UserModel(
            user_id=1,
            username='test_create_success',
            email='test@create.success',
            group_id=2,
            queue_id=3,
            birth_date=date.fromisoformat('1999-09-09')
        )

        res = yield user.delete(tx_redis)
        assert res is None

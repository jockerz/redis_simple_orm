from datetime import date

import pytest_twisted

from RSO.txredisapi.index import HashIndex
from ..data import USERS
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

        res = yield tx_redis.exists(SingleIndexUsername.redis_key())
        assert bool(res) is True
        res = yield tx_redis.exists(SingleIndexEmail.redis_key())
        assert bool(res) is True
        res = yield tx_redis.exists(SetIndexGroupID.redis_key(user))
        assert bool(res) is True
        res = yield tx_redis.exists(ListIndexQueue.redis_key(user))
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

    @pytest_twisted.inlineCallbacks
    def test_get_all_success(self, tx_redis):
        result = yield UserModel.all(tx_redis)
        assert len(result) == 0

        for data in USERS:
            user = UserModel(**data)
            yield user.save(tx_redis)

        result = yield UserModel.all(tx_redis)
        assert len(result) == len(USERS)
        assert isinstance(result[0], UserModel)


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
        """
        Validate that index data should have been remove
        as all of its model is
        """
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

            try:
                redis_key = index_class.redis_key(user)
            except TypeError:
                redis_key = index_class.redis_key()

            index_keys.append(redis_key)
            res = yield tx_redis.exists(redis_key)
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
        yield user.delete(tx_redis)

        res = yield UserModel.search(tx_redis, user.user_id)
        assert res is None

        res = yield tx_redis.exists(user.redis_key)
        assert bool(res) is False, f'res={res}'

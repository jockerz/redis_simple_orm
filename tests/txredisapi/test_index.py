from datetime import date

import pytest_twisted

from ..models.txredisapi import (
    UserModel,
    ExtendedUserModel,
    ListIndexQueue,
    SingleIndexUsername,
    SingleIndexEmail,
    SetIndexGroupID,
)


class TestListIndex:
    @pytest_twisted.inlineCallbacks
    def test_has_list_index(self, tx_redis):
        user = UserModel(
            user_id=1,
            username='test_create_success',
            email='test@create.success',
            group_id=2,
            queue_id=3,
            birth_date=date.fromisoformat('1999-09-09')
        )
        yield user.save(tx_redis)

        index = ListIndexQueue.create_from_model(user)

        res = yield index.is_exist_on_list(tx_redis, user.user_id)
        assert res is True

        res = yield tx_redis.exists(index.redis_key)
        assert bool(res) is True

        user_id_list = yield tx_redis.lrange(index.redis_key, 0, -1)
        assert user_id_list.count(user.user_id) == 1

    @pytest_twisted.inlineCallbacks
    def test_multiple_times_saved(self, tx_redis):
        user = UserModel(
            user_id=1,
            username='test_create_success',
            email='test@create.success',
            group_id=2,
            queue_id=3,
            birth_date=date.fromisoformat('1999-09-09')
        )
        yield user.save(tx_redis)

        index = ListIndexQueue.create_from_model(user)

        res = yield index.is_exist_on_list(tx_redis, user.user_id)
        assert res is True

        yield user.save(tx_redis)

        res = yield tx_redis.exists(index.redis_key)
        assert bool(res) is True

        user_id_list = yield tx_redis.lrange(index.redis_key, 0, -1)
        assert user_id_list.count(user.user_id) == 2

    @pytest_twisted.inlineCallbacks
    def test_using_extended_model_save_multiple_times(self, tx_redis):
        user = ExtendedUserModel(
            user_id=1,
            username='test_create_success',
            email='test@create.success',
            group_id=2,
            queue_id=3,
            birth_date=date.fromisoformat('1999-09-09')
        )
        yield user.save(tx_redis)
        yield user.save(tx_redis)

        index = ListIndexQueue.create_from_model(user)

        user_id_list = yield tx_redis.lrange(index.redis_key, 0, -1)
        assert user_id_list.count(user.user_id) == 1

    @pytest_twisted.inlineCallbacks
    def test_not_using_list_index(self, tx_redis):
        user = ExtendedUserModel(
            user_id=1,
            username='test_create_success',
            email='test@create.success',
            group_id=2,
            birth_date=date.fromisoformat('1999-09-09')
        )
        yield user.save(tx_redis)

        index = ListIndexQueue.create_from_model(user)

        user_id_list = yield tx_redis.lrange(index.redis_key, 0, -1)
        assert user_id_list.count(user.user_id) == 0

        res = yield index.is_exist_on_list(tx_redis, user.user_id)
        assert res is False

    @pytest_twisted.inlineCallbacks
    def test_rpushlpop(self, tx_redis):
        for data in (
            dict(user_id=1, username='uname1', queue_id=3,),
            dict(user_id=2, username='uname2', queue_id=3,),
        ):
            user = ExtendedUserModel(**data)
            yield user.save(tx_redis)

        index = ListIndexQueue.create_from_model(user)
        old_list_data = yield tx_redis.lrange(index.redis_key, 0, -1)
        assert len(old_list_data) == 2

        redis_key = index.redis_key
        user = yield ExtendedUserModel.search_by_list_rpushlpop(
            tx_redis, queue_id=3
        )
        assert isinstance(user, ExtendedUserModel)

        new_list_data = yield tx_redis.lrange(redis_key, 0, -1)
        assert len(new_list_data) == 2
        assert new_list_data[0] == old_list_data[1]
        assert new_list_data[1] == old_list_data[0]

    @pytest_twisted.inlineCallbacks
    def test_after_delete(self, tx_redis):
        user = ExtendedUserModel(
            user_id=1, username='username', queue_id=3,
        )
        yield user.save(tx_redis)
        yield user.save(tx_redis)

        index = ListIndexQueue.create_from_model(user)

        res = yield index.is_exist_on_list(tx_redis, user.user_id)
        assert res is True

        users = yield ListIndexQueue.search_models(
            tx_redis, index_value=3, model_class=ExtendedUserModel
        )
        assert len(users) == 1

        # remove here
        yield user.delete(tx_redis)

        res = yield index.is_exist_on_list(tx_redis, user.user_id)
        assert res is False

        users = yield ListIndexQueue.search_models(
            tx_redis, index_value=3, model_class=ExtendedUserModel
        )
        assert len(users) == 0


class TestHashIndex:
    @pytest_twisted.inlineCallbacks
    def test_search_model(self, tx_redis):
        user = UserModel(
            user_id=1,
            username='username',
            email='test@create.success',
        )
        yield user.save(tx_redis)

        res = yield SingleIndexUsername.search_model(
            tx_redis, user.username, UserModel
        )
        assert isinstance(res, UserModel)

        res = yield SingleIndexEmail.search_model(
            tx_redis, user.email, UserModel
        )
        assert isinstance(res, UserModel)

    @pytest_twisted.inlineCallbacks
    def search_model_not_found(self, tx_redis):
        res = yield SingleIndexUsername.search_model(
            tx_redis, 'not_exist', UserModel
        )
        assert res is None

    @pytest_twisted.inlineCallbacks
    def search_after_delete(self, tx_redis):
        user = UserModel(
            user_id=1,
            username='username',
            email='test@create.success',
        )
        yield user.save(tx_redis)

        res = yield SingleIndexUsername.search_model(
            tx_redis, user.username, UserModel
        )
        assert isinstance(res, UserModel)

        yield user.delete(tx_redis)

        res = yield SingleIndexUsername.search_model(
            tx_redis, user.username, UserModel
        )
        assert res is None


class TestSetIndex:
    @pytest_twisted.inlineCallbacks
    def test_search_model(self, tx_redis):
        user = UserModel(
            user_id=1, username='username', group_id=10
        )
        yield user.save(tx_redis)

        res = yield SetIndexGroupID.search_models(
            tx_redis, 10, UserModel
        )
        assert len(res) == 1
        assert isinstance(res[0], UserModel)

    @pytest_twisted.inlineCallbacks
    def test_on_delete_model(self, tx_redis):
        user = UserModel(
            user_id=1, username='username', group_id=10
        )
        yield user.save(tx_redis)
        yield user.delete(tx_redis)

        res = yield SetIndexGroupID.search_models(
            tx_redis, 10, UserModel
        )
        assert len(res) == 0

    @pytest_twisted.inlineCallbacks
    def test_not_found(self, tx_redis):
        res = yield SetIndexGroupID.search_models(
            tx_redis, 10, UserModel
        )
        assert len(res) == 0

from datetime import date

import pytest_twisted

from ..models.txredisapi import (
    UserModel,
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

        res = yield ListIndexQueue.has_member(tx_redis, user)
        assert res is True
        res = yield ListIndexQueue.has_member_value(
            tx_redis, user.queue_id, user.user_id
        )
        assert res is True

        res = yield tx_redis.exists(ListIndexQueue.redis_key(user))
        assert bool(res) is True

        user_id_list = yield tx_redis.lrange(
            ListIndexQueue.redis_key(user), 0, -1
        )
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

        res = yield ListIndexQueue.has_member_value(
            tx_redis, user.queue_id, user.user_id
        )
        assert res is True

        yield user.save(tx_redis)

        res = yield tx_redis.exists(ListIndexQueue.redis_key(user))
        assert bool(res) is True

        user_id_list = yield tx_redis.lrange(
            ListIndexQueue.redis_key(user), 0, -1
        )
        assert user_id_list.count(user.user_id) == 2

    @pytest_twisted.inlineCallbacks
    def test_using_extended_model_save_multiple_times(self, tx_redis):
        user = UserModel(
            user_id=1,
            username='test_create_success',
            email='test@create.success',
            group_id=2,
            queue_id=3,
            birth_date=date.fromisoformat('1999-09-09')
        )
        yield user.save(tx_redis)
        yield user.save(tx_redis)

        user_id_list = yield tx_redis.lrange(
            ListIndexQueue.redis_key(user), 0, -1
        )
        assert user_id_list.count(user.user_id) == 2

    @pytest_twisted.inlineCallbacks
    def test_not_using_list_index(self, tx_redis):
        user = UserModel(
            user_id=1,
            username='test_create_success',
            email='test@create.success',
            group_id=2,
            birth_date=date.fromisoformat('1999-09-09')
        )
        yield user.save(tx_redis)

        user_id_list = yield tx_redis.lrange(
            ListIndexQueue.redis_key(user), 0, -1
        )
        assert user_id_list.count(user.user_id) == 0

        res = yield ListIndexQueue.has_member(tx_redis, user)
        assert res is False

    @pytest_twisted.inlineCallbacks
    def test_rpushlpop(self, tx_redis):
        for data in (
            dict(user_id=1, username='uname1', queue_id=3,),
            dict(user_id=2, username='uname2', queue_id=3,),
        ):
            user = UserModel(**data)
            yield user.save(tx_redis)

        redis_key = ListIndexQueue.redis_key(user)
        old_list_data = yield tx_redis.lrange(redis_key, 0, -1)
        assert len(old_list_data) == 2

        user = yield UserModel.search_by_list_rpushlpop(
            tx_redis, queue_id=3
        )
        assert isinstance(user, UserModel)

        new_list_data = yield tx_redis.lrange(redis_key, 0, -1)
        assert len(new_list_data) == 2
        assert new_list_data[0] == old_list_data[1]
        assert new_list_data[1] == old_list_data[0]

    @pytest_twisted.inlineCallbacks
    def test_after_delete(self, tx_redis):
        user = UserModel(
            user_id=1, username='username', queue_id=3,
        )
        yield user.save(tx_redis)
        yield user.save(tx_redis)

        res = yield ListIndexQueue.has_member_value(
            tx_redis, user.queue_id, user.user_id
        )
        assert res is True

        users = yield ListIndexQueue.search_models(tx_redis, index_value=3)
        assert len(users) == 2

        # remove here
        yield user.delete(tx_redis)

        res = yield ListIndexQueue.has_member_value(
            tx_redis, user.queue_id, user.user_id
        )
        assert res is True

        users = yield ListIndexQueue.search_models(tx_redis, index_value=3)
        assert len(users) == 1


class TestHashIndex:
    @pytest_twisted.inlineCallbacks
    def test_search_model(self, tx_redis):
        user = UserModel(
            user_id=1,
            username='username',
            email='test@create.success',
        )
        yield user.save(tx_redis)

        res = yield SingleIndexUsername.search_model(tx_redis, user.username)
        assert isinstance(res, UserModel)

        res = yield SingleIndexEmail.search_model(tx_redis, user.email)
        assert isinstance(res, UserModel)

    @pytest_twisted.inlineCallbacks
    def search_model_not_found(self, tx_redis):
        res = yield SingleIndexUsername.search_model(tx_redis, 'not_exist')
        assert res is None

    @pytest_twisted.inlineCallbacks
    def search_after_delete(self, tx_redis):
        user = UserModel(
            user_id=1,
            username='username',
            email='test@create.success',
        )
        yield user.save(tx_redis)

        res = yield SingleIndexUsername.search_model(tx_redis, user.username)
        assert isinstance(res, UserModel)

        yield user.delete(tx_redis)

        res = yield SingleIndexUsername.search_model(tx_redis, user.username)
        assert res is None


class TestSetIndex:
    @pytest_twisted.inlineCallbacks
    def test_search_model(self, tx_redis):
        user = UserModel(
            user_id=1, username='username', group_id=10
        )
        yield user.save(tx_redis)

        res = yield SetIndexGroupID.search_models(tx_redis, 10)
        assert len(res) == 1
        assert isinstance(res[0], UserModel)

    @pytest_twisted.inlineCallbacks
    def test_on_delete_model(self, tx_redis):
        user = UserModel(
            user_id=1, username='username', group_id=10
        )
        yield user.save(tx_redis)
        yield user.delete(tx_redis)

        res = yield SetIndexGroupID.search_models(tx_redis, 10)
        assert len(res) == 0

    @pytest_twisted.inlineCallbacks
    def test_not_found(self, tx_redis):
        res = yield SetIndexGroupID.search_models(tx_redis, 10)

        assert isinstance(res, list)
        assert len(res) == 0

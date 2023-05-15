# WARNING: Old data might be replaced with new one without warning

# Redis Simple ORM

Redis ORM in Simple Way.

As an inspiration and a very good alternative, 
please take a look on [walrus](https://walrus.readthedocs.org).

> __NOTE__: Please be aware, Your data might be replaced without warning.


## Installation

Sync and Async with [Redis-Py](https://redis-py.readthedocs.io)

```bash
pip install redis_simple_orm[redis-py]
```

__OR__

Using [`txredisapi`](https://github.com/IlyaSkriblovsky/txredisapi)

```bash
pip install redis_simple_orm[txredisapi]
```


## Usage Example Intro

We are going to save data of users which listed on `tests/data.py`.
Please go take a look.
Copy `tests/data.py` to current directory.

Then we are going to make the __Model__ and save it to `redis`.
We also make the redis data is searchable by `id`, `username`, `email` and `group_id`.


## Usage Example

### Model

`model.py`

```python
from dataclasses import dataclass, field

from redis import Redis
from RSO.index import HashIndex, SetIndex
from RSO.model import Model

from tests.data import USERS

REDIS_MODEL_PREFIX = None


@dataclass
class UserModel(Model):
    __prefix__ = REDIS_MODEL_PREFIX
    __model_name__ = 'user'
    __key__ = 'user_id'

    user_id: int
    username: str
    email: str = field(default=None)
    group_id: int = field(default=None)

    def to_redis(self):
        result = {}
        for key, value in self.dict().items():
            # email and group_id might be None
            if value is None:
                continue
            else:
                result[key] = value
        return result

    """For easier access, we create some searching method"""

    @classmethod
    def search_by_username(cls, redis: Redis, username: str):
        return SingleIndexUsername.search_model(redis, username)

    @classmethod
    def search_by_email(cls, redis: Redis, email: str):
        return SingleIndexEmail.search_model(redis, email)

    @classmethod
    def search_group_member(cls, redis: Redis, group_id: int):
        return SetIndexGroupID.search_models(redis, group_id)


class SingleIndexUsername(HashIndex):
    __prefix__ = REDIS_MODEL_PREFIX
    __model__ = UserModel
    __key__ = 'username'


class SingleIndexEmail(HashIndex):
    __prefix__ = REDIS_MODEL_PREFIX
    __model__ = UserModel
    __key__ = 'email'


class SetIndexGroupID(SetIndex):
    __prefix__ = REDIS_MODEL_PREFIX
    __model__ = UserModel
    __key__ = 'group_id'


UserModel.__indexes__ = [
    SingleIndexUsername,
    SingleIndexEmail,
    SetIndexGroupID
]
```

### CRUD

`crud.py`
```python
import os

from redis import Redis

from tests.data import USERS
from model import UserModel


redis = Redis(
    db=int(os.getenv('REDIS_DB', 15)),
    password=os.getenv('REDIS_PASS', 'RedisPassword'),
    decode_responses=True
)


def create_user(redis: Redis, user_data: dict):
    user = UserModel(**user_data)
    user.save(redis)
    return user


def main():
    # save all user
    for user_data in USERS:
        user = create_user(redis, user_data)
        user.save(redis)

    """Now see how is the model and index data saved on redis :)"""

    # search by id
    user = UserModel.search(redis, 1)
    assert user is not None

    # search by username
    user = UserModel.search_by_username(redis, 'first_user')
    assert user is not None
    user = UserModel.search_by_username(redis, 'not_exist')
    assert user is None

    # search by email
    user = UserModel.search_by_email(redis, 'first_user@contoh.com')
    assert user is not None
    user = UserModel.search_by_email(redis, 'not_exist@contoh.com')
    assert user is None

    # search by group id
    users = UserModel.search_group_member(redis, 1)
    assert len(users) == 3
    users = UserModel.search_group_member(redis, 2)
    assert len(users) == 2
    users = UserModel.search_group_member(redis, 1_000_000)
    assert len(users) == 0


main()

```


## Usage Example (`asyncio` version, also works with `aioredis` `v.2.x`)

### Model

`model.py`

```python
from dataclasses import dataclass, field

from redis.asyncio import Redis
from RSO.asyncio.index import (
    HashIndex as AsyncHashIndex,
    SetIndex as AsyncSetIndex
)
from RSO.asyncio.model import Model as AsyncModel

from tests.data import USERS

REDIS_MODEL_PREFIX = None


@dataclass
class AsyncUserModel(AsyncModel):
    __prefix__ = REDIS_MODEL_PREFIX
    __model_name__ = 'user'
    __key__ = 'user_id'

    user_id: int
    username: str
    email: str = field(default=None)
    group_id: int = field(default=None)

    def to_redis(self):
        result = {}
        for key, value in self.dict().items():
            if value is None:
                continue
            result[key] = value
        return result

    """For easier access, we create some searching method"""

    @classmethod
    async def search_by_username(cls, redis: Redis, username: str):
        return await AsyncSingleIndexUsername.search_model(redis, username)

    @classmethod
    async def search_by_email(cls, redis: Redis, email: str):
        return await AsyncSingleIndexEmail.search_model(redis, email)

    @classmethod
    async def search_group_member(cls, redis: Redis, group_id: int):
        return await AsyncSetIndexGroupID.search_models(redis, group_id)


class AsyncSingleIndexUsername(AsyncHashIndex):
    __prefix__ = REDIS_MODEL_PREFIX
    __model__ = AsyncUserModel
    __key__ = 'username'


class AsyncSingleIndexEmail(AsyncHashIndex):
    __prefix__ = REDIS_MODEL_PREFIX
    __model__ = AsyncUserModel
    __key__ = 'email'


class AsyncSetIndexGroupID(AsyncSetIndex):
    __prefix__ = REDIS_MODEL_PREFIX
    __model__ = AsyncUserModel
    __key__ = 'group_id'


AsyncUserModel.__indexes__ = [
    AsyncSingleIndexUsername,
    AsyncSingleIndexEmail,
    AsyncSetIndexGroupID
]
```

### CRUD

`crud.py`
```python
import asyncio
import os

# from aioredis import Redis
from redis.asyncio import Redis

from tests.data import USERS
from model import AsyncUserModel


redis = Redis.from_url(
    'redis://localhost', decode_responses=True,
    db=int(os.getenv('REDIS_DB', 15)),
    password=os.getenv('REDIS_PASS', 'RedisPassword'),
)


async def main():
    # save all user
    for user_data in USERS:
        user = AsyncUserModel(**user_data)
        await user.save(redis)

    """Now see how is the model and index data saved on redis :)"""

    # search by id
    user = await AsyncUserModel.search(redis, 1)
    assert user is not None

    # search by username
    user = await AsyncUserModel.search_by_username(redis, 'first_user')
    assert user is not None
    user = await AsyncUserModel.search_by_username(redis, 'not_exist')
    assert user is None

    # search by email
    user = await AsyncUserModel.search_by_email(redis, 'first_user@contoh.com')
    assert user is not None
    user = await AsyncUserModel.search_by_email(redis, 'not_exist@contoh.com')
    assert user is None

    # search by group id
    users = await AsyncUserModel.search_group_member(redis, 1)
    assert len(users) == 3
    users = await AsyncUserModel.search_group_member(redis, 2)
    assert len(users) == 2
    users = await AsyncUserModel.search_group_member(redis, 1_000_000)
    assert len(users) == 0


asyncio.run(main())

```

## Usage Example (`twisted` version)

### Model

`model.py`

```python
from dataclasses import dataclass, field

from twisted.internet.defer import inlineCallbacks
from txredisapi import ConnectionHandler

from RSO.txredisapi.index import HashIndex, SetIndex
from RSO.txredisapi.model import Model

REDIS_MODEL_PREFIX = None


@dataclass
class UserModel(Model):
    __prefix__ = REDIS_MODEL_PREFIX
    __model_name__ = 'user'
    __key__ = 'user_id'

    user_id: int
    username: str
    email: str = field(default=None)
    group_id: int = field(default=None)

    @classmethod
    @inlineCallbacks
    def search_by_username(cls, redis: ConnectionHandler, username: str):
        result = yield SingleIndexUsername.search_model(redis, username)
        return result

    @classmethod
    @inlineCallbacks
    def search_by_email(cls, redis: ConnectionHandler, email: str):
        result = yield SingleIndexEmail.search_model(redis, email)
        return result

    @classmethod
    @inlineCallbacks
    def search_by_email(cls, redis: ConnectionHandler, group_id: int):
        result = yield SetIndexGroupID.search_models(redis, group_id)
        return result

    @classmethod
    @inlineCallbacks
    def search_group_member(cls, redis: ConnectionHandler, group_id: int):
        result = yield SetIndexGroupID.search_models(redis, group_id)
        return result


class SingleIndexUsername(HashIndex):
    __prefix__ = REDIS_MODEL_PREFIX
    __model__ = UserModel
    __key__ = 'username'


class SingleIndexEmail(HashIndex):
    __prefix__ = REDIS_MODEL_PREFIX
    __model__ = UserModel
    __key__ = 'email'


class SetIndexGroupID(SetIndex):
    __prefix__ = REDIS_MODEL_PREFIX
    __model__ = UserModel
    __key__ = 'group_id'


UserModel.__indexes__ = [
    SingleIndexUsername,
    SingleIndexEmail,
    SetIndexGroupID,
]

```


### CRUD


`crud.py`
```python
import txredisapi
from twisted.internet import reactor
from twisted.internet.defer import inlineCallbacks

from tests.data import USERS
from model import UserModel


@inlineCallbacks
def main():
    redis = yield txredisapi.Connection(dbid=15, password='RedisPassword')
    for user_data in USERS:
        user = UserModel(**user_data)
        yield user.save(redis)

    user = yield UserModel.search(redis, 1)
    assert user is not None

    # search by username
    user = yield UserModel.search_by_username(redis, 'first_user')
    assert user is not None
    user = yield UserModel.search_by_username(redis, 'not_found')
    assert user is None

    # search by email
    user = yield UserModel.search_by_email(redis, 'first_user@contoh.com')
    assert user is not None
    user = yield UserModel.search_by_email(redis, 'not_exist@contoh.com')
    assert user is None

    # search by group id
    users = yield UserModel.search_group_member(redis, 1)
    assert len(users) == 3
    users = yield UserModel.search_group_member(redis, 2)
    assert len(users) == 2
    users = yield UserModel.search_group_member(redis, 1_000_000)
    assert len(users) == 0


if __name__ == "__main__":
    main()\
        .addCallback(lambda ign: reactor.stop())\
        .addErrback(lambda ign: reactor.stop())
    reactor.run()
```
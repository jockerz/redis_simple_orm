# WARNING: Old data might be replaced with new one without warning

# Redis Simple ORM

Redis ORM in Simple Way.
If you find this module is too simple, please take a look on [walrus](https://walrus.readthedocs.org).

> __NOTE__: Please be aware, that this module is way too simple.
> Your data will likely will be replaced without warning.
> Do not use for your main data storage.

## Suggestion for this Module Usage

 - In case you need to update `index` value,
   Implement `update` method on `Model` that will remove old `index` value 
   on index data / redis, then save new `index` value


## Installation

Using [Redis-Py](https://redis-py.readthedocs.io)

```bash
pip install redis_simple_orm[redis-py]
```

__OR__

Async with [`aioredis`](https://aioredis.readthedocs.io) 
or [`redis.asyncio.Redis`](`https://redis-py.readthedocs.io/en/stable/examples/asyncio_examples.html`)

```bash
pip install redis_simple_orm[aioredis]
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

from .data import USERS


REDIS_MODEL_PREFIX = 'MY_REDIS_MODEL'


class SingleIndexUsername(HashIndex):
    __prefix__ = REDIS_MODEL_PREFIX
    __model__ = 'IndexUsername'
    __key__ = 'username'


class SingleIndexEmail(HashIndex):
    __prefix__ = REDIS_MODEL_PREFIX
    __model__ = 'IndexEmail'
    __key__ = 'email'


class SetIndexGroupID(SetIndex):
    __prefix__ = REDIS_MODEL_PREFIX
    __model__ = 'IndexGroupID'
    __key__ = 'group_id'



@dataclass
class UserModel(Model):
    __prefix__ = REDIS_MODEL_PREFIX
    __model_name__ = 'user'
    __key__ = 'user_id'
    __indexes__ = [
    	SingleIndexUsername,
    	SingleIndexEmail,
    	SetIndexGroupID
    ]

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
            result[key] = value
        return result

    """For easier access, we create some searching method"""

    @classmethod
    def search_by_username(cls, redis: Redis, username: str):
        return SingleIndexUsername.search_model(redis, username, cls)

    @classmethod
    def search_by_email(cls, redis: Redis, email: str):
        return SingleIndexEmail.search_model(redis, email, cls)

    @classmethod
    def search_group_member(cls, redis: Redis, group_id: int):
        return SetIndexGroupID.search_models(redis, group_id, cls)

```

### CRUD

`crud.py`
```python
from redis import Redis

from data import USERS
from model import UserModel


redis = Redis(decode_responses=True)


def create_user(redis: Redis, user_data: dict):
	user = UserModel(**user_data)
	user.save(redis)
	return user


def main():
	# save all user
	for user_data in USERS:
		user = create_user(redis, user_data)
		user.save()

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


## Usage Example (`asyncio` version)

### Model

`model.py`
```python
from dataclasses import dataclass, field

from aioredis import Redis
from RSO.aioredis.index import (
	HashIndex as AsyncHashIndex, 
	SetIndex as AsyncSetIndex
)
from RSO.aioredis.model import Model as AsyncModel

from data import USERS


REDIS_MODEL_PREFIX = 'MY_REDIS_MODEL'


class AsyncSingleIndexUsername(AsyncHashIndex):
    __prefix__ = REDIS_MODEL_PREFIX
    __model__ = 'IndexUsername'
    __key__ = 'username'


class AsyncSingleIndexEmail(AsyncHashIndex):
    __prefix__ = REDIS_MODEL_PREFIX
    __model__ = 'IndexEmail'
    __key__ = 'email'


class AsyncSetIndexGroupID(AsyncSetIndex):
    __prefix__ = REDIS_MODEL_PREFIX
    __model__ = 'IndexGroupID'
    __key__ = 'group_id'


@dataclass
class AsyncUserModel(AsyncModel):
    __prefix__ = REDIS_MODEL_PREFIX
    __model_name__ = 'user'
    __key__ = 'user_id'
    __indexes__ = [
    	AsyncSingleIndexUsername,
    	AsyncSingleIndexEmail,
    	AsyncSetIndexGroupID
    ]

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
        return await AsyncSingleIndexUsername.search_model(redis, username, cls)

    @classmethod
    async def search_by_email(cls, redis: Redis, email: str):
        return await AsyncSingleIndexEmail.search_model(redis, email, cls)

    @classmethod
    async def search_group_member(cls, redis: Redis, group_id: int):
        return await AsyncSetIndexGroupID.search_models(redis, group_id, cls)

```

### CRUD

`crud.py`
```python
import asyncio

from aioredis import Redis

from data import USERS
from model import AsyncUserModel


redis = Redis.from_url('redis://localhost', decode_responses=True)


async def main():
	# save all user
	for user_data in USERS:
		user =  AsyncUserModel(**user_data)
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

REDIS_MODEL_PREFIX = 'MY_REDIS_MODEL'


class SingleIndexUsername(HashIndex):
    __prefix__ = REDIS_MODEL_PREFIX
    __model__ = 'IndexUsername'
    __key__ = 'username'


class SingleIndexEmail(HashIndex):
    __prefix__ = REDIS_MODEL_PREFIX
    __model__ = 'IndexEmail'
    __key__ = 'email'


class SetIndexGroupID(SetIndex):
    __prefix__ = REDIS_MODEL_PREFIX
    __model__ = 'IndexGroupID'
    __key__ = 'group_id'


@dataclass
class UserModel(Model):
    __prefix__ = REDIS_MODEL_PREFIX
    __model_name__ = 'user'
    __key__ = 'user_id'
    
    __indexes__ = [
        SingleIndexUsername,
        SingleIndexEmail,
        SetIndexGroupID,
    ]

    user_id: int
    username: str
    email: str = field(default=None)
    group_id: int = field(default=None)

    @classmethod
    @inlineCallbacks
    def search_by_username(
        cls, redis: ConnectionHandler, username: str
    ):
        result = yield SingleIndexUsername.search_model(
            redis, username, cls 
        )
        return result

    @classmethod
    @inlineCallbacks
    def search_by_email(
        cls, redis: ConnectionHandler, email: str
    ):
        result = yield SingleIndexEmail.search_model(
            redis, email, cls 
        )
        return result

    @classmethod
    @inlineCallbacks
    def search_by_email(
        cls, redis: ConnectionHandler, group_id: int
    ):
        result = yield SetIndexGroupID.search_models(
            redis, group_id, cls 
        )
        return result
    
    @classmethod
    @inlineCallbacks
    def search_group_member(cls, redis: ConnectionHandler, group_id: int):
        result = yield SetIndexGroupID.search_models(redis, group_id, UserModel)
        return result
```


### CRUD


`crud.py`
```python
import txredisapi
from twisted.internet import reactor
from twisted.internet.defer import inlineCallbacks

from data import USERS
from model import UserModel


@inlineCallbacks
def main():
    redis = yield txredisapi.Connection()
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

# Redis Simple ORM

Redis ORM in Simple Way.
If this is too simple, please take a look on [walrus](https://walrus.readthedocs.org).

> __NOTE__: Please be aware, that this module is way too simple. 
> Do not use for your main data storage.
> Better to use for cache or temporary alike storage with redis

## Installation

[Redis-Py](https://redis-py.readthedocs.io)

```bash
pip install redis_simple_orm[redis-py]
```

__OR__

Async with [`aioredis`](https://aioredis.readthedocs.io)

```bash
pip install redis_simple_orm[aioredis]
```


## Usage Example

I need to save user data to Redis as following `python dict`.

Save as `data.py`
```python
USERS = [
	{
		'id': 1, 
		'username': 'first_user', 
		'email': 'first_user@contoh.com',
		'name': 'First User',
		'group_id': 1
	},
	{
		'id': 2, 
		'username': 'second_user', 
		'email': 'second_user@contoh.com',
		'name': 'Second User',
		'group_id': 1
	},
	{
		'id': 3, 
		'username': 'third_user', 
		'email': 'third_user@contoh.com',
		'name': 'Third User',
		'group_id': 1
	},
	{
		'id': 4, 
		'username': 'fourth_user', 
		'name': 'Fourth User',
		'group_id': 2
	},
	{
		'id': 5, 
		'username': 'fifth_user', 
		'name': 'Fifth User',
		'group_id': 2
	},
]
```


I need to save this data into Redis and make it searchable by its `id`, `username`, `email` and `group_id`.


### Model

`model.py`
```python
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



class UserModel(Model):
    __prefix__ = REDIS_MODEL_PREFIX
    __model__ = 'user'
    __key__ = 'user_id'
    __indexes__ = [
    	SingleIndexUsername,
    	SingleIndexEmail,
    	SetIndexGroupID
    ]

    user_id: int
    username: str
    email: str = None
    group_id: int

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


def create_user(user_data: dict):
	user = UserModel(**user_data)
	user.save(redis)
	return user


def main():
	# save all user
	for user_data in USERS:
		user = UserModel(**user_data)
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

### Model CRUD (Async)

`model.py`
```python
from aioredis.commands import Redis
from RSO.aioredis.index import HashIndex, SetIndex
from RSO.aioredis.model import Model

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



class UserModel(Model):
    __prefix__ = REDIS_MODEL_PREFIX
    __model__ = 'user'
    __key__ = 'user_id'
    __indexes__ = [
    	SingleIndexUsername,
    	SingleIndexEmail,
    	SetIndexGroupID
    ]

    user_id: int
    username: str
    email: str = None
    group_id: int

    """For easier access, we create some searching method"""

    @classmethod
    async def search_by_username(cls, redis: Redis, username: str):
        return await SingleIndexUsername.search_model(redis, username, cls)

    @classmethod
    async def search_by_email(cls, redis: Redis, email: str):
        return await SingleIndexEmail.search_model(redis, email, cls)

    @classmethod
    async def search_group_member(cls, redis: Redis, group_id: int):
        return await SetIndexGroupID.search_models(redis, group_id, cls)
```

### CRUD

`crud.py`
```python
import asyncio

import aioredis
from aioredis.commands import Redis

from data import USERS
from model import UserModel


redis = aioredis.from_url('redis://localhost', decode_responses=True)


async def create_user(user_data: dict):
	user = UserModel(**user_data)
	await user.save(redis)
	return user


async def main():
	# save all user
	for user_data in USERS:
		user = UserModel(**user_data)
		await user.save()

	"""Now see how is the model and index data saved on redis :)"""

	# search by id
	user = await UserModel.search(redis, 1)
	assert user is not None

	# search by username
	user = await UserModel.search_by_username(redis, 'first_user')
	assert user is not None
	user = await UserModel.search_by_username(redis, 'not_exist')
	assert user is None

	# search by email
	user = await UserModel.search_by_email(redis, 'first_user@contoh.com')
	assert user is not None
	user = await UserModel.search_by_email(redis, 'not_exist@contoh.com')
	assert user is None

	# search by group id
	users = await UserModel.search_group_member(redis, 1)
	assert len(users) == 3
	users = await UserModel.search_group_member(redis, 2)
	assert len(users) == 2
	users = await UserModel.search_group_member(redis, 1_000_000)
	assert len(users) == 0


asyncio.run(main())
```
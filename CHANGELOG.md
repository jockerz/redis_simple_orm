# Changelog

## 2.1.2

 - Minor patch for typo


## 2.1.1

 - Handling `ModuleNotFoundError` exception when importing `aioredis`


## 2.1.0

 - Add `pyopenssl` as `redis_simple_orm[txredisapi]` requirements.
 - Handling `ImportError` exception when importing `aioredis`


## 2.0.1

 - Remove `extended_save` method
 - Add `Model.all()` method on model to get all Model data


## 2.0.0 (**Breaking changes**)

 - `RSO.aioredis` to be `RSO.asyncio`
 - Add `all` method on index class
 - Remove `aioredis` from README and extra_requires.
   `aioredis` can still be used because its API is pretty similar with `redis.asyncio`
 - Index `__model__` property should be set early at Model and its Index declaration
 - remove `aioredis` v1 supports


## 1.2.7

 - Do not execute pipeline on `Model.save` if `redis` argument is instance of Pipeline


## 1.2.6

 - Allow Model and Index property `__prefix__ = None` value


## 1.2.5

 - Remove `delete self` on `Index` class


## 1.2.4

### Updated

 - `Model.search` now only load model fields from redis


## 1.2.2

### Added

 - add method `from_redis` to process redis data before loaded to `model` class. 


### Updated

 - Move `to_redis` to `base`


## 1.2.1

 - Use `BaseModel.__post_init__` convert string certain types, 
   such as `bool`, `date`, `datetime`, etc.


## 1.2.0

 - [x] Add new mode using [`txredisapi`][txredisapi]: `pip install redis_simple_orm[txredisapi]`
 - Solve some minor bugs


## 1.1.0

 - Works `aioredis` `2.x` and `>=1.3.x`


## 1.0.1

 - Minor bug patch


## 1.0.0

 - Move from [Pydantic][Pydantic] to [Dataclass][Dataclass] to reduce dependencies


## 0.x.x

 - Initial release


[Pydantic]: https://pydantic-docs.helpmanual.io/ 
[Dataclass]: https://docs.python.org/3/library/dataclasses.html
[txredisapi]: https://github.com/IlyaSkriblovsky/txredisapi

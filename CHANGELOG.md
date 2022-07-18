# Changelog

>> Note: Make sure to edit `version` on `__init__.py`


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

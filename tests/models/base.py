from dataclasses import dataclass, field
from datetime import date

from .const import REDIS_MODEL_PREFIX


class BaseIndexUsername:
    __prefix__ = REDIS_MODEL_PREFIX
    __key__ = 'username'


class BaseIndexEmail:
    __prefix__ = REDIS_MODEL_PREFIX
    __key__ = 'email'


class BaseIndexGroupID:
    __prefix__ = REDIS_MODEL_PREFIX
    __key__ = 'group_id'


class BaseIndexQueue:
    __prefix__ = REDIS_MODEL_PREFIX
    __key__ = 'queue_id'


@dataclass
class BaseUserModel:
    __prefix__ = REDIS_MODEL_PREFIX
    __model_name__ = 'user'
    __key__ = 'user_id'

    user_id: int
    username: str
    email: str = field(default=None)
    group_id: int = field(default=None)
    queue_id: int = field(default=None)
    birth_date: date = field(default=None)
    boolean: bool = field(default=False)

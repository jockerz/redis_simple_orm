from dataclasses import dataclass

from RSO.aioredis.index import HashIndex, SetIndex
from RSO.aioredis.model import Model

from .base import (
    BaseIndexGroupID,
    BaseIndexEmail,
    BaseIndexUsername,
    BaseUserModel
)


class SingleIndexUsername(BaseIndexUsername, HashIndex):
    pass


class SingleIndexEmail(BaseIndexEmail, HashIndex):
    pass


class SetIndexGroupID(BaseIndexGroupID, SetIndex):
    pass


@dataclass
class UserModel(BaseUserModel, Model):
    __indexes__ = [
        SingleIndexUsername,
        SingleIndexEmail,
        SetIndexGroupID
    ]

    def to_redis(self):
        dict_data = super(UserModel, self).to_redis()
        if self.birth_date is not None:
            dict_data['birth_date'] = self.birth_date.isoformat()
        return dict_data

from dataclasses import dataclass

from RSO.index import HashIndex, SetIndex
from RSO.model import Model

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
class UserModel(Model, BaseUserModel):
    __indexes__ = [
        SingleIndexUsername,
        SingleIndexEmail,
        SetIndexGroupID
    ]

    def to_redis(self):
        dict_data = super(UserModel, self).to_redis()
        if self.birth_date is not None:
            dict_data['birth_date'] = self.birth_date.isoformat()
        if self.email is None:
            del dict_data['email']
        return dict_data

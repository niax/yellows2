from datetime import datetime
from typing import Optional
from typing_extensions import Self

from pynamodb.attributes import ListAttribute, UTCDateTimeAttribute, UnicodeAttribute
from yellows.models.base import BaseItem

class Login(BaseItem, discriminator="LOGIN"):
    login_id = UnicodeAttribute(attr_name='LoginId')
    last_login = UTCDateTimeAttribute(attr_name="LastLogin", null=True)
    scope = ListAttribute(attr_name="Scope", of=UnicodeAttribute)

    @classmethod
    def create(cls, login_id:str) -> Self:
        key = cls._build_key(login_id)
        return cls(
            key, sk=key,
            login_id=login_id,
            scope=[],
        )

    @classmethod
    def get_by_login_id(cls, login_id:str, consistent_read:bool=False) -> Optional[Self]:
        key = cls._build_key(login_id)
        return cls.get(hash_key=key, range_key=key, consistent_read=consistent_read)

    def update_last_login(self):
        self.update([
            Login.last_login.set(datetime.now()),
        ], condition=Login.pk.exists() & Login.sk.exists())

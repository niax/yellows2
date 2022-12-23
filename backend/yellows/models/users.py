from typing_extensions import Self
from pynamodb.attributes import NumberAttribute, UnicodeAttribute
from yellows.models.base import BaseItem

class User(BaseItem, discriminator="USER"):
    _nick_name = UnicodeAttribute(attr_name='NickName')
    full_name = UnicodeAttribute(attr_name='FullName')
    event_count = NumberAttribute(attr_name='EventCount')
    _achievement_score = NumberAttribute(attr_name='AchievementScore')

    @property
    def nick_name(self) -> str:
        return self._nick_name

    def _set_achievement_score(self, score:int):
        self._achievement_score = score
        self._fix_sort_order()

    def _get_achievement_score(self) -> int:
        return int(self._achievement_score)
    achievement_score = property(_get_achievement_score, _set_achievement_score)

    @classmethod
    def _calculate_sort_order(cls, achievement_score:float, nick_name:str) -> int:
        achievement_score = int(achievement_score)
        nick_slice = 12
        name_bytes = nick_name.encode('utf-8')[:nick_slice]
        bits = (achievement_score & 0xffffffff) << (nick_slice * 8)
        for i, byte in enumerate(name_bytes):
            bits |= (byte << ((nick_slice - i - 1) * 8))
        return bits

    @classmethod
    def create(cls, nick_name:str, full_name:str) -> Self:
        key = cls._build_key(nick_name)
        return cls(
            key, sk=key,
            _nick_name=nick_name,
            full_name=full_name,
            event_count=0,
            _achievement_score=0,
            type_='USER',
            index_sort_order=cls._calculate_sort_order(0, nick_name),
        )

    @classmethod
    def stub(cls, nick_name: str) -> Self:
        key = cls._build_key(nick_name)
        return cls(key, sk=key)

    def _fix_sort_order(self):
        self.index_sort_order = self._calculate_sort_order(self.achievement_score, self.nick_name)

    @classmethod
    def get_by_nick_name(cls, nick_name:str, consistent_read:bool=False) -> Self:
        key = cls._build_key(nick_name)
        return cls.get(hash_key=key, range_key=key, consistent_read=consistent_read)

from datetime import datetime
from typing_extensions import Self

from pynamodb.attributes import BooleanAttribute, NumberAttribute, UTCDateTimeAttribute, UnicodeAttribute
from pynamodb.pagination import ResultIterator

from yellows.models.base import BaseItem
from yellows.models.users import User

class Event(BaseItem, discriminator="EVENT"):
    short_name = UnicodeAttribute(attr_name="ShortName")
    long_name = UnicodeAttribute(attr_name="LongName")
    starts_at = UTCDateTimeAttribute(attr_name="StartsAt")
    ends_at = UTCDateTimeAttribute(attr_name="EndsAt")
    attendee_count = NumberAttribute(attr_name="AttendeeCount", null=True)
    yellow_count = NumberAttribute(attr_name="YellowCount", null=True)

    @classmethod
    def create(cls, short_name: str, long_name: str, starts_at: datetime, ends_at: datetime) -> Self:
        key = cls._build_key(short_name)
        ordering = starts_at.timestamp()
        return cls(
            key, sk=key,
            short_name=short_name,
            long_name=long_name,
            starts_at=starts_at,
            ends_at=ends_at,
            type_='EVENT',
            index_sort_order=ordering,
        )

    @classmethod
    def stub(cls, short_name: str) -> Self:
        key = cls._build_key(short_name)
        return cls(key, sk=key)

    @classmethod
    def get_by_short_name(cls, short_name:str, consistent_read:bool=False) -> Self:
        key = cls._build_key(short_name)
        return cls.get(hash_key=key, range_key=key, consistent_read=consistent_read)


class EventBooking(BaseItem, discriminator='EVENTBOOKING'):
    user_nick_name = UnicodeAttribute(attr_name="UserNickName")
    user_full_name = UnicodeAttribute(attr_name="UserFullName")
    event_short_name = UnicodeAttribute(attr_name="EventShortName")
    event_long_name = UnicodeAttribute(attr_name="EventLongName")
    eta = UnicodeAttribute(attr_name="EventEta")
    etd = UnicodeAttribute(attr_name="EventEtd")
    role = UnicodeAttribute(attr_name="EventRole", null=True)
    is_team_lead = BooleanAttribute(attr_name="IsEventTeamLead")

    @classmethod
    def create(cls, event:Event, user:User, eta:str, etd:str) -> Self:
        return cls(
            event.pk, sk=user.pk,
            event_short_name=event.short_name,
            event_long_name=event.long_name,
            user_nick_name=user.nick_name,
            user_full_name=user.full_name,
            eta=eta,
            etd=etd,
            is_team_lead=False,
        )

    @classmethod
    def list_bookings_for_user(cls, user:User) -> ResultIterator[Self]:
        return cls.inverted_index.query(user.pk, range_key_condition=cls.pk.startswith('EVENT_'))

    @classmethod
    def list_bookings_for_event(cls, event:Event) -> ResultIterator[Self]:
        return cls.query(event.pk, range_key_condition=cls.sk.startswith("USER_"))

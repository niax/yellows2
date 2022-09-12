from dataclasses import dataclass
from datetime import datetime
from typing import Optional, cast
from typing_extensions import Self

from dynamodb_json import json_util as ddb_json

@dataclass
class Event:
    short_name: str
    long_name: str
    starts_at: datetime
    ends_at: datetime
    venue_id: Optional[str]
    attendee_count: Optional[int]
    yellow_count: Optional[int]

    @classmethod
    def from_ddb(cls, ddb_item) -> Self:
        item = ddb_json.loads(ddb_item)
        starts_at = datetime.fromisoformat(item['StartsAt'])
        ends_at = datetime.fromisoformat(item['EndsAt'])
        return Event(
            short_name=item['ShortName'],
            long_name=item['LongName'],
            starts_at=starts_at,
            ends_at=ends_at,
            venue_id=item.get('VenueId'),
            attendee_count=item.get('AttendeeCount'),
            yellow_count=item.get('YellowCount'),
        )

    @classmethod
    def make_key(cls, short_name):
        key = f'EVENT_{short_name}'
        return cast(dict, ddb_json.dumps({
            'PK': key,
            'SK': key,
        }, as_dict=True))

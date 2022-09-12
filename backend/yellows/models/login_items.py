from dataclasses import dataclass
from datetime import datetime
from typing import List, cast

from dynamodb_json import json_util as ddb_json

@dataclass
class Login:
    login_id: str
    scope: List[str]
    last_login: datetime

    @classmethod
    def from_ddb(cls, ddb_item):
        item = ddb_json.loads(ddb_item)
        return Login(
            login_id=item['LoginId'],
            scope=item['Scope'],
            last_login=item['LastLogin'],
        )

    @classmethod
    def make_key(cls, login_id):
        key = f'LOGIN_{login_id}'
        return cast(dict, ddb_json.dumps({
            'PK': key,
            'SK': key,
        }, as_dict=True))

from datetime import datetime
from typing import List, Optional, cast
from typing_extensions import Self
from dataclasses import dataclass

from dynamodb_json import json_util as ddb_json
from mypy_boto3_dynamodb.client import DynamoDBClient
from yellows.config import get_config

@dataclass
class Login:
    login_id: str
    scope: List[str]
    last_login: datetime

class LoginModel:
    @classmethod
    def load_from_config(cls) -> Self:
        config = get_config()
        return cls(
            config.boto_session.client('dynamodb'),
            config.get_dynamo_table_name())

    def __init__(self, ddb_client: DynamoDBClient, table_name: str):
        self.ddb_client = ddb_client
        self.table_name = table_name

    def _get_key(self, login_id) -> dict:
        key = f'LOGIN_{login_id}'
        return cast(dict, ddb_json.dumps({
            'PK': key,
            'SK': key,
        }, as_dict=True))

    def get_login(self, login_id) -> Optional[Login]:
        key = self._get_key(login_id)
        ddb_item = self.ddb_client.get_item(
            TableName=self.table_name,
            Key=key,
        ).get('Item')

        if ddb_item is None:
            return None

        item = ddb_json.loads(ddb_item)
        return Login(
            login_id=item['LoginId'],
            scope=item['Scope'],
            last_login=item['LastLogin'],
        )

    def update_last_login(self, login_id):
        key = self._get_key(login_id)
        self.ddb_client.update_item(
            TableName=self.table_name,
            Key=key,
            UpdateExpression='SET #0=:0',
            ConditionExpression='attribute_exists(PK)',
            ExpressionAttributeNames={
                '#0': 'LastLogin',
            },
            ExpressionAttributeValues={
                ':0': {'S': datetime.now().isoformat()},
            },
        )

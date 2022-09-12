from datetime import datetime
from typing import Optional 
from typing_extensions import Self

from mypy_boto3_dynamodb.client import DynamoDBClient
from yellows.config import get_config
from yellows.models.login_items import Login

class LoginDao:
    @classmethod
    def load_from_config(cls) -> Self:
        config = get_config()
        return cls(
            config.boto_session.client('dynamodb'),
            config.get_dynamo_table_name())

    def __init__(self, ddb_client: DynamoDBClient, table_name: str):
        self.ddb_client = ddb_client
        self.table_name = table_name

    def get_login(self, login_id) -> Optional[Login]:
        key = Login.make_key(login_id)
        ddb_item = self.ddb_client.get_item(
            TableName=self.table_name,
            Key=key,
        ).get('Item')

        if ddb_item is None:
            return None
        
        return Login.from_ddb(ddb_item)

    def update_last_login(self, login_id):
        key = Login.make_key(login_id)
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

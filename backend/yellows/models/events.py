from typing import List, Optional, Tuple
from typing_extensions import Self
from mypy_boto3_dynamodb.client import DynamoDBClient

from yellows.config import get_config
from yellows.crypto import get_crypto
from yellows.models.base import *
from yellows.models.event_items import Event
from yellows.powertools import tracer

class EventDao:
    @classmethod
    def load_from_config(cls) -> Self:
        config = get_config()
        return cls(
            config.boto_session.client('dynamodb'),
            config.get_dynamo_table_name())

    def __init__(self, ddb_client: DynamoDBClient, table_name: str):
        self.ddb_client = ddb_client
        self.table_name = table_name
        self.crypto_helper = get_crypto()

    @tracer.capture_method(capture_response=False)
    def list_events(self, max_items:int=10, next_token:Optional[str]=None) -> Tuple[List[Event], Optional[str]]:
        kwargs = {}
        if next_token is not None:
            kwargs['ExclusiveStartKey'] = self.crypto_helper.decrypt_dict(next_token)
        query_result = self.ddb_client.query(
            TableName=self.table_name,
            IndexName=GSI_TYPE_ORDERED,
            KeyConditionExpression="#0=:0",
            ExpressionAttributeNames={
                '#0': 'Type',
            },
            ExpressionAttributeValues={
                ':0': {"S": 'EVENT'},
            },
            ScanIndexForward=False,
            Limit=max_items,
            **kwargs,
        )
        events = []
        for item in query_result['Items']:
            events.append(Event.from_ddb(item))
        next_token = None
        last_key = query_result.get('LastEvaluatedKey')
        if last_key is not None:
            next_token = self.crypto_helper.encrypt_dict(last_key)
        return events, next_token

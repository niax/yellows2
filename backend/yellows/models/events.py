from typing import List
from typing_extensions import Self
from mypy_boto3_dynamodb.client import DynamoDBClient

from yellows.config import get_config
from yellows.models.base import *
from yellows.models.event_items import Event

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

    # TODO: Pagination!
    def list_events(self) -> List[Event]:
        query_paginator = self.ddb_client.get_paginator('query')
        page_iterator = query_paginator.paginate(
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
        )
        events = []
        for page in page_iterator:
            for item in page['Items']:
                events.append(Event.from_ddb(item))
        return events

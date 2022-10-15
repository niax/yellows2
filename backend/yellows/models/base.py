from typing_extensions import Self
from mypy_boto3_dynamodb.client import DynamoDBClient

from yellows.config import get_config
from yellows.crypto import CryptoHelper, get_crypto

GSI_FLIPPED = 'InvertedIndex'
GSI_TYPE_ORDERED = 'TypeIndexOrder'

class BaseDao:
    @classmethod
    def load_from_config(cls) -> Self:
        config = get_config()
        crypto_helper = get_crypto()
        return cls(
            config.boto_session.client('dynamodb'),
            config.get_dynamo_table_name(),
            crypto_helper)

    def __init__(self, ddb_client: DynamoDBClient, table_name: str, crypto_helper: CryptoHelper):
        self.ddb_client = ddb_client
        self.table_name = table_name
        self.crypto_helper = crypto_helper

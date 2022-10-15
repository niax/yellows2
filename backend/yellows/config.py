from functools import cached_property
import os
import boto3
import json
from aws_lambda_powertools.logging import Logger
from mypy_boto3_secretsmanager.client import SecretsManagerClient
from mypy_boto3_dynamodb.client import DynamoDBClient

logger = Logger()

class Config:
    @cached_property
    def boto_session(self):
        return boto3.Session()

    @property
    def domain_name(self) -> str:
        return os.environ['DOMAIN_NAME']

    @property
    def kms_key_arn(self) -> str:
        return os.environ['KMS_KEY_ARN']

    @cached_property
    def dynamodb_client(self) -> DynamoDBClient:
        return self.boto_session.client('dynamodb')

    @cached_property
    def secrets_manager_client(self) -> SecretsManagerClient:
        return self.boto_session.client('secretsmanager')

    def _get_secret_dict(self, envvar) -> dict:
        secret_id = os.environ[envvar]
        logger.info("Fetching %s (%s)", secret_id, envvar)
        secret = self.secrets_manager_client.get_secret_value(
            SecretId=secret_id,
        )
        return json.loads(secret['SecretString'])

    @cached_property
    def _discord_oauth_secret(self) -> dict:
        return self._get_secret_dict('DISCORD_OAUTH2_SECRET_ARN')

    @property
    def discord_oauth_client_id(self) -> str:
        return self._discord_oauth_secret['clientId']

    @property
    def discord_oauth_client_secret(self) -> str:
        return self._discord_oauth_secret['clientSecret']

    @cached_property
    def _jwt_secret(self) -> dict:
        return self._get_secret_dict('JWT_SECRET_ARN')

    @property
    def jwt_public_key(self) -> str:
        return self._jwt_secret['publicKey']

    @property
    def jwt_private_key(self) -> str:
        return self._jwt_secret['privateKey']

    def get_dynamo_table_name(self) -> str:
        return os.environ['DDB_TABLE_NAME']

_config = None
def get_config() -> Config:
    global _config
    if _config is None:
        _config = Config()
    return _config


from base64 import urlsafe_b64decode, urlsafe_b64encode
import json
import aws_encryption_sdk

from yellows.config import get_config
from yellows.powertools import tracer

class CryptoHelper:
    def __init__(self):
        self.config = get_config()
        self.crypto_client = aws_encryption_sdk.EncryptionSDKClient()
        self.key_provider = aws_encryption_sdk.StrictAwsKmsMasterKeyProvider(key_ids=[
            self.config.kms_key_arn,
        ])

    @tracer.capture_method(capture_response=False)
    def encrypt(self, s: str) -> str:
        cyphertext, _ = self.crypto_client.encrypt(
            source=s.encode('utf-8'),
            key_provider=self.key_provider,
        )
        return urlsafe_b64encode(cyphertext).decode('utf-8')

    @tracer.capture_method(capture_response=False)
    def decrypt(self, s: str) -> str:
        b = urlsafe_b64decode(s)
        plaintext, _ = self.crypto_client.decrypt(
            source=b,
            key_provider=self.key_provider,
        )
        return plaintext.decode('utf-8')

    def encrypt_dict(self, d: dict) -> str:
        s = json.dumps(d)
        return self.encrypt(s)

    def decrypt_dict(self, cyphertext: str) -> dict:
        plaintext = self.decrypt(cyphertext)
        return json.loads(plaintext)

_crypto = None
def get_crypto() -> CryptoHelper:
    global _crypto
    if _crypto is None:
        _crypto = CryptoHelper()
    return _crypto

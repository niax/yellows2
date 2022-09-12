from datetime import datetime, timedelta
from functools import wraps
import inspect
from authlib.integrations.requests_client import OAuth2Session
from authlib.jose import JsonWebToken
from authlib.jose.errors import BadSignatureError
from aws_lambda_powertools.event_handler.api_gateway import Router
from aws_lambda_powertools.event_handler.exceptions import UnauthorizedError
from aws_lambda_powertools.logging import Logger
from urllib.parse import urlunparse
from http.cookies import SimpleCookie

from yellows.config import get_config

router = Router()
logger = Logger()
jwt = JsonWebToken(['RS256'])
DISCORD_AUTH_URL = 'https://discord.com/oauth2/authorize'
DISCORD_TOKEN_URL = 'https://discord.com/api/oauth2/token'
DISCORD_GET_SELF_INFO_URL = 'https://discord.com/api/users/@me'

class Auth:
    def __init__(self):
        self.config = get_config()

    def _get_client(self):
        redirect_uri = urlunparse((
            'https', self.config.domain_name, '/api/auth/login-finish',
            None, None, None))
        
        return OAuth2Session(
            self.config.discord_oauth_client_id, self.config.discord_oauth_client_secret,
            redirect_uri=redirect_uri, scope='identify email')

    def create_authorization_url(self):
        client = self._get_client()
        auth_url, _ = client.create_authorization_url(DISCORD_AUTH_URL)
        return auth_url

    def make_jwt_for_discord(self, request_url):
        client = self._get_client()
        # Prime the client with the token
        client.fetch_token(DISCORD_TOKEN_URL, authorization_response=request_url)
        me_resp = client.get(DISCORD_GET_SELF_INFO_URL)
        me = me_resp.json()
        now = datetime.utcnow()
        exp = now + timedelta(seconds=86400)
        claims = {
            'iss': self.config.domain_name,
            'sub': '{}@discord'.format(me['id']),
            'exp': exp.isoformat(),
            'scope': [
                'event-admin',
            ],
        }
        return jwt.encode({'alg': 'RS256'}, claims, self.config.jwt_private_key).decode('utf-8')

    def check_auth(self, required_scopes):
        cookies = SimpleCookie(router.current_event.headers.get('Cookie', ''))
        auth_cookie = cookies.get('yellows-auth')
        if auth_cookie is None:
            raise UnauthorizedError("Missing auth cookie")
        try:
            claims = jwt.decode(auth_cookie.value, self.config.jwt_public_key, claims_options={
                'iss': {
                    'essential': True,
                    'values': [self.config.domain_name],
                },
                'sub': { 'essential': True },
                'exp': { 'essential': True },
                'scope': { 'essential': True },
            })
        except BadSignatureError:
            logger.error("Failed to validate JWT", exc_info=True)
            raise UnauthorizedError("Invalid JWT")
        # Check Expiry
        expiry = datetime.fromisoformat(claims['exp'])
        if expiry < datetime.now():
            raise UnauthorizedError("Session expired")
        # Check that user has valid scopes
        scopes = set(claims['scope'])
        has_all_scopes = all(s in scopes for s in required_scopes)
        if not has_all_scopes:
            logger.warn("User missing scopes")
            raise UnauthorizedError("Insufficient access")
        # TODO: Get a user object
        return claims

_auth = None
def get_auth() -> Auth:
    global _auth
    if _auth is None:
        _auth = Auth()
    return _auth

def auth_required(*required_claims):
    def _deco(f):
        signature = inspect.signature(f)
        takes_user = 'user' in signature.parameters 

        @wraps(f)
        def _inner(*args, **kwargs):
            authn = get_auth()
            authn.check_auth(required_claims)
            if takes_user:
                kwargs['user'] = authn.check_auth(required_claims)
            return f(*args, **kwargs)
        return _inner
    return _deco
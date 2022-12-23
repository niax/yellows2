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

from aws_lambda_powertools.metrics import MetricUnit

from yellows.config import get_config
from yellows.models import Login
from yellows.powertools import metrics, tracer

router = Router()
logger = Logger()
jwt = JsonWebToken(['RS256'])
DISCORD_AUTH_URL = 'https://discord.com/oauth2/authorize'
DISCORD_TOKEN_URL = 'https://discord.com/api/oauth2/token'
DISCORD_GET_SELF_INFO_URL = 'https://discord.com/api/users/@me'

def _record_login(login: Login):
    metrics.add_metadata("user", login.login_id)
    tracer.put_annotation('user', login.login_id)

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

    def login(self, request_url):
        discord_info = self._get_discord_info_from_callback(request_url)
        login_id = f'{discord_info["id"]}@discord'
        logger.warn("Attempted login for '%s'", login_id)
        login = self._get_and_record_login(login_id)
        _record_login(login)
        return self._make_jwt_for_login(login)

    def _get_and_record_login(self, login_id) -> Login:
        login = Login.get_by_login_id(login_id)
        if login is None:
            raise UnauthorizedError("No permit!")
        login.update_last_login()
        return login

    @tracer.capture_method(capture_response=False)
    def _get_discord_info_from_callback(self, request_url):
        client = self._get_client()
        try:
            # Prime the client with the token
            client.fetch_token(DISCORD_TOKEN_URL, authorization_response=request_url)
            me_resp = client.get(DISCORD_GET_SELF_INFO_URL)
            return me_resp.json()
        except Exception:
            logger.exception("Failed callback from Discord")
            raise UnauthorizedError("Failed callback from Discord")

    def _make_jwt_for_login(self, login: Login):
        now = datetime.utcnow()
        exp = now + timedelta(seconds=86400)
        claims = {
            'iss': self.config.domain_name,
            'sub': login.login_id,
            'exp': exp.isoformat(),
            'scope': login.scope,
        }
        return jwt.encode({'alg': 'RS256'}, claims, self.config.jwt_private_key).decode('utf-8')

    @tracer.capture_method(capture_response=False)
    def check_auth(self, required_scopes) -> Login:
        denied = 0
        try:
            return self._check_auth(required_scopes)
        except UnauthorizedError as ue:
            denied = 1
            raise ue
        finally:
            metrics.add_metric('Unauthorized', MetricUnit.Count, denied)


    def _check_auth(self, required_scopes) -> Login:
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
            logger.exception("Failed to validate JWT")
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
        # TODO: Do we need this, can we just read out the JWT?
        login = Login.get_by_login_id(claims['sub'])
        if login is None:
            raise UnauthorizedError("Insufficient access")
        return login

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
            user = authn.check_auth(required_claims)
            _record_login(user)
            if takes_user:
                kwargs['user'] = user
            return f(*args, **kwargs)
        return _inner
    return _deco

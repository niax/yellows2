from aws_lambda_powertools.event_handler import Response
from aws_lambda_powertools.event_handler.api_gateway import Router
from aws_lambda_powertools.logging import Logger
from aws_lambda_powertools.tracing import Tracer
from yellows.auth import get_auth
from yellows.powertools import annotate_operation
from yellows.request_helpers import get_request_url

tracer = Tracer()
router = Router()
logger = Logger()

# TODO: make these POSTs?
@router.get('/logout')
@annotate_operation
def logout_get():
    return Response(
        status_code=302, headers={
            'Location': '/',
            'Set-Cookie': 'yellows-auth=dead; Max-Age=0; Path=/',
        },
        content_type='text/plain', body="Redir..")

@router.get('/login')
@annotate_operation
def login_get():
    authn = get_auth()
    # Construct a redirect URL
    auth_url = authn.create_authorization_url()
    return Response(
        status_code=302, headers={'Location': auth_url},
        content_type='text/plain', body="Redir..")

@router.get('/login-finish')
@annotate_operation
def login_redir_get():
    authn = get_auth()
    # Build the original URL
    request_url = get_request_url()
    auth_token = authn.login(request_url)

    return Response(
        status_code=302, headers={
            'Location': '/',
            'Set-Cookie': 'yellows-auth={}; Max-Age=86400; Path=/'.format(auth_token),
        },
        content_type='text/plain', body='Redir...',
    )

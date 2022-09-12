
from urllib.parse import urlencode, urlunparse
from aws_lambda_powertools.event_handler.api_gateway import Router

from yellows.settings import get_config


router = Router()

def get_request_url():
    config = get_config()
    query_params = router.current_event.query_string_parameters
    query_params_str = None
    if query_params is not None:
        query_params_str = urlencode(query_params)
    return urlunparse((
        'https', config.domain_name, router.current_event.path,
        None, query_params_str, None))

from aws_lambda_powertools.event_handler.api_gateway import Router
from aws_lambda_powertools.tracing import Tracer

from yellows.auth import auth_required

tracer = Tracer()
router = Router()

@router.get('/')
@auth_required()
def get():
    return {"foo": "bar"}

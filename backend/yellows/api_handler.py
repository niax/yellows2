from aws_lambda_powertools.event_handler import APIGatewayRestResolver
from aws_lambda_powertools.logging import Logger, correlation_paths
from aws_lambda_powertools.tracing import Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext

from . import views

tracer = Tracer()
tracer.patch()
logger = Logger()

app = APIGatewayRestResolver()

app.include_router(views.events.router, '/api/events')
app.include_router(views.auth.router, '/api/auth')

@logger.inject_lambda_context(correlation_id_path=correlation_paths.API_GATEWAY_REST)
@tracer.capture_lambda_handler
def lambda_handler(event: dict, context: LambdaContext) -> dict:
    logger.info("Event: %s", event)
    return app.resolve(event, context)

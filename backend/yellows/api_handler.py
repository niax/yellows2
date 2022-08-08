from aws_lambda_powertools.logging import Logger, correlation_paths
from aws_lambda_powertools.tracing import Tracer
from aws_lambda_powertools.event_handler import APIGatewayRestResolver
from aws_lambda_powertools.utilities.typing import LambdaContext

tracer = Tracer()
logger = Logger()

app = APIGatewayRestResolver()

@app.get('/')
@tracer.capture_method
def get():
    return {"foo": "bar"}

@logger.inject_lambda_context(correlation_id_path=correlation_paths.API_GATEWAY_REST)
@tracer.capture_lambda_handler
def lambda_handler(event: dict, context: LambdaContext) -> dict:
    logger.info("event: %s", event)
    return app.resolve(event, context)

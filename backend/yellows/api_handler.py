from datetime import datetime
from aws_lambda_powertools.event_handler import APIGatewayRestResolver
from aws_lambda_powertools.logging import Logger, correlation_paths
from aws_lambda_powertools.metrics import MetricUnit
from aws_lambda_powertools.utilities.typing import LambdaContext

from yellows.powertools import tracer, metrics

from . import views

logger = Logger()

app = APIGatewayRestResolver()

app.include_router(views.events.router, '/api/events')
app.include_router(views.users.router, '/api/users')
app.include_router(views.auth.router, '/api/auth')

@logger.inject_lambda_context(correlation_id_path=correlation_paths.API_GATEWAY_REST)
@metrics.log_metrics(capture_cold_start_metric=True)
@tracer.capture_lambda_handler
def lambda_handler(event: dict, context: LambdaContext) -> dict:
    t_start = datetime.now()
    logger.info("Event: %s", event)
    fault = 0
    try:
        ret = app.resolve(event, context)
        return ret
    except Exception as e:
        logger.exception("Exception thrown while processing event")
        fault = 1
        raise e
    finally:
        duration = datetime.now() - t_start
        metrics.add_metric('Time', MetricUnit.Milliseconds, duration.total_seconds() * 1000.0)
        metrics.add_metric('Fault', MetricUnit.Count, fault)

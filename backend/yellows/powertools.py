from aws_lambda_powertools.tracing import Tracer
from aws_lambda_powertools.metrics import Metrics

tracer = Tracer()
tracer.patch()
metrics = Metrics()

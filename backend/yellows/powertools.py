from functools import wraps
from aws_lambda_powertools.tracing import Tracer
from aws_lambda_powertools.metrics import Metrics

tracer = Tracer()
tracer.patch()
metrics = Metrics()

def annotate_operation(f):
    op_name = '.'.join([f.__module__, f.__name__])

    @wraps(f)
    def _inner(*args, **kwargs):
        metrics.add_dimension('operation', op_name)
        tracer.put_annotation('operation', op_name)
        return f(*args, **kwargs)
    return _inner

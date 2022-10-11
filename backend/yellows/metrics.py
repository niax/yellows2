from datetime import datetime
from functools import wraps
from aws_lambda_powertools.metrics import Metrics
from aws_lambda_powertools.metrics.base import MetricUnit

def with_metrics(f):
    metrics = Metrics()
    op_name = '.'.join([f.__module__, f.__name__])

    @wraps(f)
    @metrics.log_metrics
    def _inner(*args, **kwargs):
        t_start = datetime.now()
        metrics.add_dimension('Operation', op_name)
        kwargs['metrics'] = metrics
        ret = f(*args, **kwargs)
        duration = datetime.now() - t_start
        metrics.add_metric('Time', MetricUnit.Milliseconds, duration.total_seconds() / 1000.0)
        return ret
    return _inner

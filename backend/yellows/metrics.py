from functools import wraps
from yellows.powertools import metrics, tracer

def with_metrics(f):
    op_name = '.'.join([f.__module__, f.__name__])

    @wraps(f)
    def _inner(*args, **kwargs):
        metrics.add_dimension('operation', op_name)
        tracer.put_annotation('operation', op_name)
        return f(*args, **kwargs)
    return _inner

import functools
from aws_lambda_powertools.event_handler.api_gateway import Router
from aws_lambda_powertools.logging import Logger

from yellows.auth import auth_required
from yellows.models import Event
from yellows.powertools import annotate_operation
from yellows.views.common import wrap_list_iterable

router = Router()
logger = Logger()

def _translate_event(event: Event) -> dict:
    return {
        'short_name': event.short_name,
        'long_name': event.long_name,
        'attendee_count': event.attendee_count,
        'yellow_count': event.yellow_count,
        'starts_at': event.starts_at.isoformat(),
        'ends_at': event.ends_at.isoformat(),
    }

@router.get('/')
@auth_required()
@annotate_operation
def list():
    return wrap_list_iterable(functools.partial(Event.list_ordered), _translate_event, 'events')

@router.post('/')
@auth_required('event-admin')
@annotate_operation
def post(user=None):
    return user.__dict__

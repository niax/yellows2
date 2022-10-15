from aws_lambda_powertools.event_handler.api_gateway import Router
from aws_lambda_powertools.logging import Logger

from yellows.auth import auth_required
from yellows.models import YellowsModel
from yellows.powertools import annotate_operation

router = Router()
logger = Logger()

@router.get('/')
@auth_required()
@annotate_operation
def get():
    dao = YellowsModel.get().events
    max_items_str = router.current_event.get_query_string_value('max_items')
    if max_items_str is None:
        max_items_str = '10'
    max_items = int(max_items_str)
    next_token = router.current_event.get_query_string_value('next_token')
    logger.info("Why? '%s'", next_token)

    json_events = []
    events, next_token = dao.list_events(max_items=max_items, next_token=next_token)
    for event in events:
        json_events.append({
            'short_name': event.short_name,
            'long_name': event.long_name,
            'attendee_count': event.attendee_count,
            'yellow_count': event.yellow_count,
            'starts_at': event.starts_at.isoformat(),
            'ends_at': event.ends_at.isoformat(),
        })
    return {
        'events': json_events,
        'next_token': next_token,
    }

@router.post('/')
@auth_required('event-admin')
@annotate_operation
def post(user=None):
    return user.__dict__

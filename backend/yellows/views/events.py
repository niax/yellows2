from aws_lambda_powertools.event_handler.api_gateway import Router
from aws_lambda_powertools.tracing import Tracer

from yellows.auth import auth_required
from yellows.models import YellowsModel

tracer = Tracer()
router = Router()

@router.get('/')
@auth_required()
def get():
    dao = YellowsModel.get().events
    jsoned = []
    for event in dao.list_events():
        jsoned.append({
            'short_name': event.short_name,
            'long_name': event.long_name,
            'attendee_count': event.attendee_count,
            'yellow_count': event.yellow_count,
            'starts_at': event.starts_at.isoformat(),
            'ends_at': event.ends_at.isoformat(),
        })
    return jsoned 

@router.post('/')
@auth_required('event-admin')
def post(user=None):
    return user.__dict__

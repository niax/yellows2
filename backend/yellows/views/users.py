import functools
from aws_lambda_powertools.event_handler.api_gateway import Router
from aws_lambda_powertools.logging import Logger

from yellows.auth import auth_required
from yellows.models.users import User
from yellows.powertools import annotate_operation
from yellows.views.common import wrap_list_iterable


router = Router()
logger = Logger()

def _translate_user(user: User) -> dict:
    return {
        'nick_name': user.nick_name,
        'full_name': user.full_name,
        'event_count': user.event_count,
        'achievement_score': user.achievement_score,
    }

@router.get('/')
@auth_required()
@annotate_operation
def list():
    return wrap_list_iterable(functools.partial(User.list_ordered, scan_index_forward=False), _translate_user, 'users')

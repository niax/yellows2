
from typing import Any, Callable, Optional, Protocol, TypeVar, cast
from aws_lambda_powertools.event_handler.api_gateway import Router
from aws_lambda_powertools.event_handler.exceptions import BadRequestError
from pynamodb.pagination import ResultIterator

from yellows.crypto import get_crypto

router = Router()


def _try_convert_int(s: str, name: str) -> int:
    try:
        return int(s)
    except:
        raise BadRequestError(f"{name} is not a number") 

T = TypeVar("T")
class PynamoGeneratorPartial(Protocol[T]):
    def __call__(self, limit:Optional[int]=None, last_evaluated_key:Optional[dict]=None) -> ResultIterator[T]: # type: ignore
        pass

def wrap_list_iterable(partial: PynamoGeneratorPartial[T], translation: Callable[[T], dict], items_key: str):
    max_items = router.current_event.get_query_string_value('max_items')
    if max_items is not None:
        max_items = _try_convert_int(cast(str, max_items), 'max_items')

    next_token = router.current_event.get_query_string_value('next_token')
    last_key = None
    if next_token is not None:
        crypto_helper = get_crypto()
        try:
            last_key = crypto_helper.decrypt_dict(next_token)
        except:
            raise BadRequestError(f"Bad next_token") 

    iterable = partial(limit=max_items, last_evaluated_key=last_key)
    json_objects = []
    for i in iterable:
        json_objects.append(translation(i))

    ret: Any = {
        items_key: json_objects,
        'next_token': None,
    }
    if iterable.last_evaluated_key:
        crypto_helper = get_crypto()
        ret['next_token'] = crypto_helper.encrypt_dict(iterable.last_evaluated_key)
    return ret

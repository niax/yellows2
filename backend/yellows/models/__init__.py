from functools import cached_property
from typing_extensions import Self

from yellows.models.events import EventDao
from yellows.models.event_items import *
from yellows.models.login import LoginDao
from yellows.models.login_items import *

yellows_model = None
class YellowsModel:
    @classmethod
    def get(cls) -> Self:
        global yellows_model
        if yellows_model is None:
            yellows_model = YellowsModel()
        return yellows_model

    @cached_property
    def login(self) -> LoginDao:
        return LoginDao.load_from_config()

    @cached_property
    def events(self) -> EventDao:
        return EventDao.load_from_config()

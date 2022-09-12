from functools import cached_property
from typing_extensions import Self

from yellows.models.login import Login, LoginModel

yellows_model = None
class YellowsModel:
    @classmethod
    def get(cls) -> Self:
        global yellows_model
        if yellows_model is None:
            yellows_model = YellowsModel()
        return yellows_model

    @cached_property
    def login(self) -> LoginModel:
        return LoginModel.load_from_config()

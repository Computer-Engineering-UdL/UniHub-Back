from __future__ import annotations

from pydantic import BaseModel

from app.schemas import (
    auth,
    channel,
    housing_category,
    housing_offer,
    housing_photo,
    interest,
    user,
)
from app.schemas.auth import *  # noqa
from app.schemas.channel import *  # noqa
from app.schemas.housing_category import *  # noqa
from app.schemas.housing_offer import *  # noqa
from app.schemas.housing_photo import *  # noqa
from app.schemas.interest import *  # noqa
from app.schemas.user import *  # noqa

for module in (
    housing_offer,
    housing_category,
    housing_photo,
    interest,
    channel,
    user,
    auth,
):
    for name in dir(module):
        obj = getattr(module, name)
        if isinstance(obj, type) and issubclass(obj, BaseModel):
            try:
                obj.model_rebuild()
            except AttributeError:
                pass

__all__ = (
    channel.__all__
    + housing_offer.__all__
    + housing_category.__all__
    + housing_photo.__all__
    + interest.__all__
    + user.__all__
    + auth.__all__
)

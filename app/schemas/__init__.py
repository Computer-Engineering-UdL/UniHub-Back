from __future__ import annotations

from pydantic import BaseModel

from app.schemas.auth import *  # noqa
from app.schemas.channel import *  # noqa
from app.schemas.connection import *  # noqa
from app.schemas.conversation import *  # noqa
from app.schemas.file_association import *  # noqa
from app.schemas.files import *  # noqa
from app.schemas.housing_amenity import *  # noqa
from app.schemas.housing_category import *  # noqa
from app.schemas.housing_offer import *  # noqa
from app.schemas.interest import *  # noqa
from app.schemas.message import *  # noqa
from app.schemas.report import *  # noqa
from app.schemas.terms import *  # noqa
from app.schemas.user import *  # noqa
from app.schemas.user_like import *  # noqa
from app.schemas.user_terms_acceptance import *  # noqa

from . import (
    auth,
    channel,
    connection,
    conversation,
    file_association,
    files,
    housing_amenity,
    housing_category,
    housing_offer,
    interest,
    message,
    report,
    terms,
    user,
    user_like,
    user_terms_acceptance,
)

for module in (
    housing_offer,
    housing_category,
    housing_amenity,
    interest,
    channel,
    user,
    auth,
    message,
    conversation,
    user_like,
    files,
    file_association,
    terms,
    user_terms_acceptance,
    connection,
    report,
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
    + housing_amenity.__all__
    + interest.__all__
    + user.__all__
    + auth.__all__
    + message.__all__
    + conversation.__all__
    + user_like.__all__
    + files.__all__
    + file_association.__all__
    + terms.__all__
    + user_terms_acceptance.__all__
    + connection.__all__
    + report.__all__
)

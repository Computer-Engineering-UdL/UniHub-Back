from app.schemas.channel import ChannelBase, ChannelCreate, ChannelRead, ChannelUpdate, MembershipRead
from app.schemas.housing_category import (
    HousingCategoryBase,
    HousingCategoryCreate,
    HousingCategoryDetail,
    HousingCategoryList,
    HousingCategoryRead,
    HousingCategoryUpdate,
)
from app.schemas.housing_offer import (
    HousingOfferBase,
    HousingOfferCreate,
    HousingOfferDetail,
    HousingOfferRead,
    HousingOfferUpdate,
)
from app.schemas.housing_photo import (
    HousingPhotoBase,
    HousingPhotoCreate,
    HousingPhotoDetail,
    HousingPhotoRead,
    HousingPhotoUpdate,
)

from app.schemas.interest import InterestCategoryRead, InterestRead, UserInterestCreate
from app.schemas.user import UserCreate, UserList, UserPasswordChange, UserRead

from app.schemas.auth import AuthResponse, LoginRequest, Token, TokenData  # isort: skip
from app.schemas.housing_offer import HousingOfferList  # isort: skip
from app.schemas.housing_photo import HousingPhotoList  # isort: skip

# Rebuild models to resolve forward references
HousingOfferDetail.model_rebuild()
HousingOfferList.model_rebuild()
HousingOfferRead.model_rebuild()
HousingOfferUpdate.model_rebuild()
HousingOfferCreate.model_rebuild()
HousingOfferBase.model_rebuild()

HousingCategoryList.model_rebuild()
HousingCategoryRead.model_rebuild()
HousingCategoryUpdate.model_rebuild()
HousingCategoryCreate.model_rebuild()
HousingCategoryBase.model_rebuild()
HousingCategoryDetail.model_rebuild()

HousingPhotoDetail.model_rebuild()
HousingPhotoBase.model_rebuild()
HousingPhotoCreate.model_rebuild()
HousingPhotoUpdate.model_rebuild()
HousingPhotoRead.model_rebuild()
HousingPhotoList.model_rebuild()

InterestCategoryRead.model_rebuild()
InterestRead.model_rebuild()

ChannelRead.model_rebuild()
ChannelCreate.model_rebuild()
ChannelUpdate.model_rebuild()
MembershipRead.model_rebuild()
UserRead.model_rebuild()
UserList.model_rebuild()
UserCreate.model_rebuild()
UserPasswordChange.model_rebuild()
AuthResponse.model_rebuild()
LoginRequest.model_rebuild()

# Exported names
__all__ = [
    # Housing Offer Schemas
    "HousingOfferBase",
    "HousingOfferCreate",
    "HousingOfferUpdate",
    "HousingOfferRead",
    "HousingOfferList",
    "HousingOfferDetail",
    # Housing Category Schemas
    "HousingCategoryBase",
    "HousingCategoryCreate",
    "HousingCategoryUpdate",
    "HousingCategoryRead",
    "HousingCategoryList",
    "HousingCategoryDetail",
    # Housing Photo Schemas
    "HousingPhotoBase",
    "HousingPhotoCreate",
    "HousingPhotoUpdate",
    "HousingPhotoRead",
    "HousingPhotoList",
    "HousingPhotoDetail",
    "ChannelRead",
    "ChannelBase",
    "ChannelCreate",
    "ChannelUpdate",
    "MembershipRead",
    "AuthResponse",
    "UserList",
    "UserCreate",
    "UserRead",
    "UserPasswordChange",
    "LoginRequest",
    "TokenData",
    "Token",
    "InterestCategoryRead",
    "InterestRead",
    "UserInterestCreate",
]
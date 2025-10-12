# Schemas package initialization
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
    HousingOfferList,
    HousingOfferRead,
    HousingOfferUpdate,
)
from app.schemas.housing_photo import (
    HousingPhotoBase,
    HousingPhotoCreate,
    HousingPhotoDetail,
    HousingPhotoList,
    HousingPhotoRead,
    HousingPhotoUpdate,
)

# Rebuild models to resolve forward references
HousingOfferDetail.model_rebuild()
HousingCategoryDetail.model_rebuild()
HousingPhotoDetail.model_rebuild()

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
]

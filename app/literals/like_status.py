from enum import Enum


class LikeStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class LikeTargetType(str, Enum):
    HOUSING_OFFER = "housing_offer"
    JOB_OFFER = "job_offer"
    ITEM = "item"


__all__ = ["LikeStatus", "LikeTargetType"]
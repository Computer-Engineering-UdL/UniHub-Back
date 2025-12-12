from enum import Enum


class ItemCondition(str, Enum):
    NEW = "New"
    LIKE_NEW = "Like New"
    GOOD = "Good"
    FAIR = "Fair"
    POOR = "Poor"


class ItemStatus(str, Enum):
    ACTIVE = "active"
    SOLD = "sold"
    RESERVED = "reserved"
    INACTIVE = "inactive"


class ItemSort(str, Enum):
    NEWEST = "newest"
    PRICE_ASC = "price_asc"
    PRICE_DESC = "price_desc"

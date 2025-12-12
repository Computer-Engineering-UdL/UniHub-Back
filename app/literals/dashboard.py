from enum import Enum


class TimeRange(str, Enum):
    WEEK = "week"
    MONTH = "month"
    TRIMESTER = "trimester"
    YEAR = "year"

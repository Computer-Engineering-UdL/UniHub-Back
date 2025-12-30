from .channels import seed_channels
from .housing_offers import seed_housing_data
from .interests import seed_interests
from .items import seed_items
from .job_offers import seed_job_offers
from .reports import seed_reports
from .university import seed_universities
from .users import seed_users

__all__ = [
    "seed_interests",
    "seed_users",
    "seed_channels",
    "seed_housing_data",
    "seed_universities",
    "seed_reports",
    "seed_items",
    "seed_job_offers",
]

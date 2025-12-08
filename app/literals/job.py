from enum import Enum


class JobCategory(str, Enum):
    TECHNOLOGY = "Technology"
    MARKETING = "Marketing"
    DESIGN = "Design"
    SALES = "Sales"
    FINANCE = "Finance"
    HUMAN_RESOURCES = "Human Resources"
    CUSTOMER_SERVICE = "Customer Service"
    ENGINEERING = "Engineering"
    EDUCATION = "Education"
    HEALTHCARE = "Healthcare"
    OTHER = "Other"


class JobType(str, Enum):
    FULL_TIME = "Full-time"
    PART_TIME = "Part-time"
    INTERNSHIP = "Internship"
    FREELANCE = "Freelance"


class JobWorkplace(str, Enum):
    ON_SITE = "On-site"
    HYBRID = "Hybrid"
    REMOTE = "Remote"

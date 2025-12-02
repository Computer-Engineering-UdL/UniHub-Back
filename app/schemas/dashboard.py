from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class DashboardStat(BaseModel):
    label: str
    value: int | float
    change_percentage: float
    trend: str


class DashboardStatsResponse(BaseModel):
    total_users: DashboardStat
    active_content: DashboardStat
    pending_reports: DashboardStat
    engagement_rate: DashboardStat


class ChartDataset(BaseModel):
    label: str
    data: List[int | float]


class ChartResponse(BaseModel):
    labels: List[str]
    datasets: List[ChartDataset]


class ActivityItem(BaseModel):
    id: str
    type: str
    title: str
    description: str
    timestamp: datetime
    user_avatar: Optional[str] = None

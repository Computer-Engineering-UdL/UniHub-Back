from datetime import datetime
from typing import List, Optional, Union

from pydantic import BaseModel, ConfigDict


class DashboardStat(BaseModel):
    label: str
    value: Union[int, float]
    change_percentage: float
    trend: str


class DashboardStatsResponse(BaseModel):
    total_users: DashboardStat
    active_content: DashboardStat
    total_channels: DashboardStat
    engagement_rate: DashboardStat


class ChartDataset(BaseModel):
    label: str
    data: List[Union[int, float]]


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
    model_config = ConfigDict(from_attributes=True)

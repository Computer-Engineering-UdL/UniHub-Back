from datetime import datetime, timedelta
from typing import List

from sqlalchemy.orm import Session

from app.schemas.dashboard import (
    ActivityItem,
    ChartDataset,
    ChartResponse,
    DashboardStat,
    DashboardStatsResponse,
)

from .dashboard_repository import DashboardRepository


class DashboardService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = DashboardRepository(db)

    def _calculate_trend(self, current_val: int, previous_val: int) -> str:
        if current_val > previous_val:
            return "up"
        elif current_val < previous_val:
            return "down"
        return "neutral"

    def _calculate_percentage_change(self, current: int, previous: int) -> float:
        if previous == 0:
            return 100.0 if current > 0 else 0.0
        return ((current - previous) / previous) * 100

    def get_stats(self) -> DashboardStatsResponse:
        now = datetime.now()
        thirty_days_ago = now - timedelta(days=30)
        sixty_days_ago = now - timedelta(days=60)

        # Users
        total_users = self.repository.count_users()
        new_users_last_30 = self.repository.count_users_created_after(thirty_days_ago)
        new_users_prev_30 = self.repository.count_users_created_between(sixty_days_ago, thirty_days_ago)

        user_trend = self._calculate_trend(new_users_last_30, new_users_prev_30)
        user_change = self._calculate_percentage_change(new_users_last_30, new_users_prev_30)

        # Housing
        total_housing = self.repository.count_housing_offers()
        housing_last_30 = self.repository.count_housing_offers_created_after(thirty_days_ago)
        housing_prev_30 = self.repository.count_housing_offers_created_between(sixty_days_ago, thirty_days_ago)

        content_trend = self._calculate_trend(housing_last_30, housing_prev_30)
        content_change = self._calculate_percentage_change(housing_last_30, housing_prev_30)

        # Engagement
        verified_users = self.repository.count_verified_users()
        engagement_rate = (verified_users / total_users * 100) if total_users > 0 else 0.0

        pending_reports = 0

        return DashboardStatsResponse(
            total_users=DashboardStat(
                label="Total Users", value=total_users, change_percentage=round(user_change, 1), trend=user_trend
            ),
            active_content=DashboardStat(
                label="Active Housing",
                value=total_housing,
                change_percentage=round(content_change, 1),
                trend=content_trend,
            ),
            pending_reports=DashboardStat(
                label="Pending Reports", value=pending_reports, change_percentage=0, trend="neutral"
            ),
            engagement_rate=DashboardStat(
                label="Verified Users %", value=round(engagement_rate, 1), change_percentage=0, trend="neutral"
            ),
        )

    def get_content_distribution(self) -> ChartResponse:
        housing_count = self.repository.count_housing_offers()
        marketplace_count = 0
        jobs_count = 0
        return ChartResponse(
            labels=["Housing", "Marketplace", "Jobs"],
            datasets=[ChartDataset(label="Content Distribution", data=[housing_count, marketplace_count, jobs_count])],
        )

    def get_weekly_activity(self) -> ChartResponse:
        today = datetime.now()
        labels = []
        new_users_data = []
        posts_data = []

        for i in range(6, -1, -1):
            day = today - timedelta(days=i)
            labels.append(day.strftime("%a"))
            start_day = day.replace(hour=0, minute=0, second=0, microsecond=0)
            end_day = day.replace(hour=23, minute=59, second=59, microsecond=999999)

            u_count = self.repository.count_users_created_between(start_day, end_day)
            p_count = self.repository.count_housing_offers_created_between(start_day, end_day)

            new_users_data.append(u_count)
            posts_data.append(p_count)

        return ChartResponse(
            labels=labels,
            datasets=[
                ChartDataset(label="New Users", data=new_users_data),
                ChartDataset(label="New Housing", data=posts_data),
            ],
        )

    def get_recent_activity(self, limit: int = 5) -> List[ActivityItem]:
        users = self.repository.get_recent_users(limit)
        offers = self.repository.get_recent_housing_offers(limit)

        activity_list = []

        for u in users:
            activity_list.append(
                ActivityItem(
                    id=str(u.id),
                    type="new_user",
                    title="New User",
                    description=f"{u.username} joined UniRoom",
                    timestamp=u.created_at,
                    user_avatar=u.avatar_url,
                )
            )

        for o in offers:
            offer_title = getattr(o, "title", "New Housing Offer")
            offer_city = getattr(o, "city", "Unknown City")

            activity_list.append(
                ActivityItem(
                    id=str(o.id),
                    type="new_post",
                    title=offer_title,
                    description=f"New offer in {offer_city}",
                    timestamp=o.posted_date,
                    user_avatar=None,
                )
            )

        activity_list.sort(key=lambda x: x.timestamp, reverse=True)

        return activity_list[:limit]

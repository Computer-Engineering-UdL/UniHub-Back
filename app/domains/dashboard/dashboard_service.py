from datetime import datetime, timedelta
from typing import List

from sqlalchemy.orm import Session

from app.literals.dashboard import TimeRange
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
        total_users = self.repository.count_users()
        new_users_last_30 = self.repository.count_users_created_after(thirty_days_ago)
        new_users_prev_30 = self.repository.count_users_created_between(sixty_days_ago, thirty_days_ago)
        user_trend = self._calculate_trend(new_users_last_30, new_users_prev_30)
        user_change = self._calculate_percentage_change(new_users_last_30, new_users_prev_30)
        total_channels = self.repository.count_channels()
        total_housing = self.repository.count_housing_offers()
        active_content_val = total_housing + total_channels
        housing_last_30 = self.repository.count_housing_offers_created_after(thirty_days_ago)
        housing_prev_30 = self.repository.count_housing_offers_created_between(sixty_days_ago, thirty_days_ago)
        content_trend = self._calculate_trend(housing_last_30, housing_prev_30)
        content_change = self._calculate_percentage_change(housing_last_30, housing_prev_30)
        verified_users = self.repository.count_verified_users()
        engagement_rate = (verified_users / total_users * 100) if total_users > 0 else 0.0

        return DashboardStatsResponse(
            total_users=DashboardStat(
                label="Total Users", value=total_users, change_percentage=round(user_change, 1), trend=user_trend
            ),
            active_content=DashboardStat(
                label="Active Content",
                value=active_content_val,
                change_percentage=round(content_change, 1),
                trend=content_trend,
            ),
            total_channels=DashboardStat(
                label="Total Channels", value=total_channels, change_percentage=0, trend="neutral"
            ),
            engagement_rate=DashboardStat(
                label="Verified Users %", value=round(engagement_rate, 1), change_percentage=0, trend="neutral"
            ),
        )

    def get_content_distribution(self) -> ChartResponse:
        """Pie Chart: Housing vs Channels (vs Jobs/Marketplace in future)."""
        housing_count = self.repository.count_housing_offers()
        channels_count = self.repository.count_channels()
        return ChartResponse(
            labels=["Housing Offers", "Channels"],
            datasets=[ChartDataset(label="Content Distribution", data=[housing_count, channels_count])],
        )

    def get_channels_distribution(self) -> ChartResponse:
        raw_data = self.repository.count_channels_by_type()

        labels = []
        data = []

        for channel_type, count in raw_data:
            labels.append(channel_type.capitalize())
            data.append(count)

        if not data:
            labels = ["No Channels"]
            data = [0]

        return ChartResponse(labels=labels, datasets=[ChartDataset(label="Channels by Type", data=data)])

    def get_activity_chart(self, time_range: TimeRange) -> ChartResponse:
        now = datetime.now()
        labels = []
        new_users_data = []
        activity_data = []

        if time_range == TimeRange.YEAR:
            for i in range(11, -1, -1):
                month_start = (now.replace(day=1) - timedelta(days=32 * i)).replace(day=1)
                labels.append(month_start.strftime("%b"))
                start_date = month_start.replace(hour=0, minute=0, second=0)
                end_date = (start_date + timedelta(days=31)).replace(day=1) - timedelta(seconds=1)
                u_count = self.repository.count_users_created_between(start_date, end_date)
                h_count = self.repository.count_housing_offers_created_between(start_date, end_date)
                m_count = self.repository.count_messages_created_in_range(start_date, end_date)
                new_users_data.append(u_count)
                activity_data.append(h_count + m_count)

        else:
            days_map = {TimeRange.WEEK: 7, TimeRange.MONTH: 30, TimeRange.TRIMESTER: 90}
            days_count = days_map.get(time_range, 7)
            step = 1
            if time_range == TimeRange.TRIMESTER:
                step = 5

            for i in range(days_count - 1, -1, -step):
                day = now - timedelta(days=i)
                labels.append(day.strftime("%d %b"))
                start_date = day.replace(hour=0, minute=0, second=0, microsecond=0)
                end_date = day + timedelta(days=step) - timedelta(seconds=1)
                u_count = self.repository.count_users_created_between(start_date, end_date)
                h_count = self.repository.count_housing_offers_created_between(start_date, end_date)
                m_count = self.repository.count_messages_created_in_range(start_date, end_date)
                new_users_data.append(u_count)
                activity_data.append(h_count + m_count)

        return ChartResponse(
            labels=labels,
            datasets=[
                ChartDataset(label="New Users", data=new_users_data),
                ChartDataset(label="Activity (Posts & Messages)", data=activity_data),
            ],
        )

    def get_recent_activity(self, limit: int = 50) -> List[ActivityItem]:
        users = self.repository.get_recent_users(limit)
        offers = self.repository.get_recent_housing_offers(limit)
        channels = self.repository.get_recent_channels(limit)
        messages = self.repository.get_recent_messages(limit)
        activity_list = []
        for u in users:
            activity_list.append(
                ActivityItem(
                    id=str(u.id),
                    type="new_user",
                    title="New User Joined",
                    description=f"{u.username} has joined the platform",
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
                    description=f"New offer posted in {offer_city}",
                    timestamp=o.posted_date,
                    user_avatar=None,
                )
            )

        for c in channels:
            activity_list.append(
                ActivityItem(
                    id=str(c.id),
                    type="new_channel",
                    title="New Channel Created",
                    description=f"Channel #{c.name} ({c.channel_type}) is now active",
                    timestamp=c.created_at,
                    user_avatar=None,
                )
            )

        for m in messages:
            activity_list.append(
                ActivityItem(
                    id=str(m.id),
                    type="new_message",
                    title="New Message",
                    description="New message in channel...",
                    timestamp=m.created_at,
                    user_avatar=None,
                )
            )
        activity_list.sort(key=lambda x: x.timestamp, reverse=True)

        return activity_list[:limit]

import random
from datetime import datetime, timedelta
from typing import List, Optional

from sqlalchemy.orm import Session

from app.literals.report import ReportCategory, ReportPriority, ReportReason, ReportStatus
from app.literals.users import Role
from app.models import Channel, HousingOfferTableModel, User
from app.models.report import Report


def seed_reports(
    db: Session,
    users: List[User],
    channels: Optional[List[Channel]] = None,
    messages=None,
    housing_offers: Optional[List[HousingOfferTableModel]] = None,
) -> List[Report]:
    """Create sample reports for testing the moderation system using real content IDs."""

    if len(users) < 3:
        print("* Skipping report seeding - not enough users")
        return []

    existing = db.query(Report).first()
    if existing:
        print("* Reports already seeded")
        return []

    if channels is None:
        channels = db.query(Channel).all()
    if housing_offers is None:
        housing_offers = db.query(HousingOfferTableModel).all()

    all_reports = []
    now = datetime.now()

    regular_users = [u for u in users if u.role != Role.ADMIN.value]
    admin_users = [u for u in users if u.role == Role.ADMIN.value]

    if len(regular_users) < 2:
        print("* Not enough regular users for report seeding")
        return []

    report_templates = []

    if housing_offers:
        for i, offer in enumerate(housing_offers[:3]):
            reasons = [
                (
                    ReportReason.FAKE_LISTING,
                    "This listing has fake photos. The address doesn't match.",
                    ReportPriority.HIGH,
                ),
                (
                    ReportReason.SCAM_FRAUD,
                    "User asked for deposit without showing the property. Suspicious behavior.",
                    ReportPriority.CRITICAL,
                ),
                (ReportReason.SPAM, "Same listing posted multiple times with different titles.", ReportPriority.LOW),
            ]
            reason, desc, priority = reasons[i % len(reasons)]
            report_templates.append(
                {
                    "content_type": ReportCategory.HOUSING.value,
                    "content_id": str(offer.id),
                    "content_title": offer.title,
                    "reason": reason.value,
                    "description": desc,
                    "priority": priority.value,
                    "days_ago": 5 - i,
                    "reported_user_id": offer.user_id,
                }
            )

    if channels:
        for i, channel in enumerate(channels[:3]):
            reasons = [
                (
                    ReportReason.SPAM,
                    "Channel is being used to post repetitive promotional content.",
                    ReportPriority.MEDIUM,
                ),
                (
                    ReportReason.INAPPROPRIATE_CONTENT,
                    "Channel contains content that violates community guidelines.",
                    ReportPriority.HIGH,
                ),
                (
                    ReportReason.HARASSMENT,
                    "Channel is being used to target and harass specific users.",
                    ReportPriority.HIGH,
                ),
            ]
            reason, desc, priority = reasons[i % len(reasons)]
            report_templates.append(
                {
                    "content_type": ReportCategory.CHANNELS.value,
                    "content_id": str(channel.id),
                    "content_title": channel.name,
                    "reason": reason.value,
                    "description": desc,
                    "priority": priority.value,
                    "days_ago": 3 + i,
                }
            )

    for i, user in enumerate(regular_users[:4]):
        reasons = [
            (
                ReportReason.INAPPROPRIATE_CONTENT,
                "Profile contains inappropriate images that violate community guidelines.",
                ReportPriority.HIGH,
            ),
            (
                ReportReason.HATE_SPEECH,
                "User posting hateful comments targeting a specific group.",
                ReportPriority.CRITICAL,
            ),
            (
                ReportReason.HARASSMENT,
                "User is sending repeated unwanted messages and being aggressive.",
                ReportPriority.HIGH,
            ),
            (
                ReportReason.SPAM,
                "User is spamming promotional content across multiple channels.",
                ReportPriority.MEDIUM,
            ),
        ]
        reason, desc, priority = reasons[i % len(reasons)]
        report_templates.append(
            {
                "content_type": ReportCategory.USER.value,
                "content_id": str(user.id),
                "content_title": f"User: {user.username}",
                "reason": reason.value,
                "description": desc,
                "priority": priority.value,
                "days_ago": 4 + i,
                "reported_user_id": user.id,
            }
        )

    if housing_offers and len(housing_offers) > 3:
        offer = housing_offers[3]
        report_templates.append(
            {
                "content_type": ReportCategory.HOUSING.value,
                "content_id": str(offer.id),
                "content_title": offer.title,
                "reason": ReportReason.FAKE_LISTING.value,
                "description": "Photos don't match the actual property.",
                "priority": ReportPriority.MEDIUM.value,
                "status": ReportStatus.REVIEWING.value,
                "days_ago": 8,
                "reported_user_id": offer.user_id,
            }
        )

    if channels and len(channels) > 5:
        channel = channels[5]
        report_templates.append(
            {
                "content_type": ReportCategory.CHANNELS.value,
                "content_id": str(channel.id),
                "content_title": channel.name,
                "reason": ReportReason.SPAM.value,
                "description": "Channel is flooded with MLM recruitment messages.",
                "priority": ReportPriority.LOW.value,
                "status": ReportStatus.DISMISSED.value,
                "resolution": "Content was borderline. Warning issued to channel admins.",
                "days_ago": 12,
            }
        )

    if len(regular_users) > 4:
        user = regular_users[4]
        report_templates.append(
            {
                "content_type": ReportCategory.USER.value,
                "content_id": str(user.id),
                "content_title": f"User: {user.username}",
                "reason": ReportReason.SCAM_FRAUD.value,
                "description": "User sold fake concert tickets. Event security denied entry.",
                "priority": ReportPriority.HIGH.value,
                "status": ReportStatus.RESOLVED.value,
                "resolution": "Full refund provided. User banned.",
                "days_ago": 20,
                "reported_user_id": user.id,
            }
        )

    for template in report_templates:
        reported_user_id = template.pop("reported_user_id", None)
        available_reporters = [u for u in regular_users if u.id != reported_user_id]
        if not available_reporters:
            available_reporters = regular_users

        reporter = random.choice(available_reporters)

        if reported_user_id is None:
            reported = random.choice([u for u in regular_users if u.id != reporter.id])
            reported_user_id = reported.id

        created_at = now - timedelta(days=template.get("days_ago", 0))
        status = template.get("status", ReportStatus.PENDING.value)

        report = Report(
            reported_by_id=reporter.id,
            reported_user_id=reported_user_id,
            content_type=template["content_type"],
            content_id=template["content_id"],
            content_title=template.get("content_title"),
            reason=template["reason"],
            description=template.get("description"),
            status=status,
            priority=template["priority"],
            created_at=created_at,
            updated_at=created_at,
        )

        if status in [ReportStatus.RESOLVED.value, ReportStatus.DISMISSED.value]:
            if admin_users:
                report.reviewed_by_id = random.choice(admin_users).id
                report.reviewed_at = created_at + timedelta(days=1)
                report.resolution = template.get("resolution")
        elif status == ReportStatus.REVIEWING.value:
            if admin_users:
                report.reviewed_by_id = random.choice(admin_users).id

        db.add(report)
        all_reports.append(report)

    db.flush()
    print(f"* {len(all_reports)} sample reports created for moderation testing")
    return all_reports

import random
from datetime import datetime, timedelta
from typing import List

from sqlalchemy.orm import Session

from app.literals.report import ReportCategory, ReportPriority, ReportReason, ReportStatus
from app.literals.users import Role
from app.models import User
from app.models.report import Report


def seed_reports(db: Session, users: List[User]) -> List[Report]:
    """Create sample reports for testing the moderation system."""

    if len(users) < 3:
        print("* Skipping report seeding - not enough users")
        return []

    existing = db.query(Report).first()
    if existing:
        print("* Reports already seeded")
        return []

    all_reports = []
    now = datetime.now()

    report_templates = [
        {
            "content_type": ReportCategory.HOUSING.value,
            "content_id": "housing-listing-001",
            "content_title": "Cozy Studio Near Campus",
            "reason": ReportReason.FAKE_LISTING.value,
            "description": "This listing has fake photos taken from another website. The address doesn't exist.",
            "priority": ReportPriority.HIGH.value,
            "days_ago": 5,
        },
        {
            "content_type": ReportCategory.HOUSING.value,
            "content_id": "housing-listing-002",
            "content_title": "Affordable Room in Shared Apartment",
            "reason": ReportReason.SCAM_FRAUD.value,
            "description": "User asked for deposit without showing the room. Suspicious behavior.",
            "priority": ReportPriority.CRITICAL.value,
            "days_ago": 2,
        },
        {
            "content_type": ReportCategory.MARKETPLACE.value,
            "content_id": "marketplace-item-101",
            "content_title": "Used MacBook Pro 2021",
            "reason": ReportReason.SCAM_FRAUD.value,
            "description": "Seller disappeared after receiving payment. Never delivered the item.",
            "priority": ReportPriority.CRITICAL.value,
            "days_ago": 1,
        },
        {
            "content_type": ReportCategory.MARKETPLACE.value,
            "content_id": "marketplace-item-102",
            "content_title": "Textbook Bundle",
            "reason": ReportReason.SPAM.value,
            "description": "Same listing posted multiple times to flood the marketplace.",
            "priority": ReportPriority.LOW.value,
            "days_ago": 7,
        },
        {
            "content_type": ReportCategory.CHANNELS.value,
            "content_id": "channel-msg-201",
            "content_title": "Message in Campus Announcements",
            "reason": ReportReason.SPAM.value,
            "description": "Posting unrelated promotional content in announcement channel.",
            "priority": ReportPriority.MEDIUM.value,
            "days_ago": 3,
        },
        {
            "content_type": ReportCategory.MESSAGES.value,
            "content_id": "dm-msg-301",
            "content_title": "Direct Message",
            "reason": ReportReason.HARASSMENT.value,
            "description": "User is sending repeated unwanted messages and being aggressive.",
            "priority": ReportPriority.HIGH.value,
            "days_ago": 1,
        },
        {
            "content_type": ReportCategory.USER.value,
            "content_id": "user-profile-401",
            "content_title": "User: suspicious_account123",
            "reason": ReportReason.INAPPROPRIATE_CONTENT.value,
            "description": "Profile contains inappropriate images that violate community guidelines.",
            "priority": ReportPriority.HIGH.value,
            "days_ago": 4,
        },
        {
            "content_type": ReportCategory.USER.value,
            "content_id": "user-profile-402",
            "content_title": "User: angry_poster",
            "reason": ReportReason.HATE_SPEECH.value,
            "description": "User posting hateful comments targeting a specific group.",
            "priority": ReportPriority.CRITICAL.value,
            "days_ago": 0,
        },
        {
            "content_type": ReportCategory.SERVICES.value,
            "content_id": "service-listing-501",
            "content_title": "Tutoring Services",
            "reason": ReportReason.SCAM_FRAUD.value,
            "description": "Advertises tutoring but asks for payment upfront and doesn't deliver.",
            "priority": ReportPriority.MEDIUM.value,
            "days_ago": 6,
        },
        {
            "content_type": ReportCategory.SERVICES.value,
            "content_id": "service-listing-502",
            "content_title": "Resume Writing Service",
            "reason": ReportReason.OTHER.value,
            "description": "Service quality is extremely poor. Possible outsourcing to bots.",
            "priority": ReportPriority.LOW.value,
            "days_ago": 10,
        },
        {
            "content_type": ReportCategory.HOUSING.value,
            "content_id": "housing-listing-003",
            "content_title": "Single Room Downtown",
            "reason": ReportReason.FAKE_LISTING.value,
            "description": "Photos don't match the actual property.",
            "priority": ReportPriority.MEDIUM.value,
            "status": ReportStatus.REVIEWING.value,
            "days_ago": 8,
        },
        {
            "content_type": ReportCategory.MESSAGES.value,
            "content_id": "dm-msg-302",
            "content_title": "Threatening Direct Message",
            "reason": ReportReason.VIOLENCE.value,
            "description": "User sent threatening messages about physical harm.",
            "priority": ReportPriority.CRITICAL.value,
            "status": ReportStatus.RESOLVED.value,
            "resolution": "User has been permanently banned from the platform.",
            "days_ago": 15,
        },
        {
            "content_type": ReportCategory.MARKETPLACE.value,
            "content_id": "marketplace-item-103",
            "content_title": "Concert Tickets",
            "reason": ReportReason.SCAM_FRAUD.value,
            "description": "Tickets were fake. Event security denied entry.",
            "priority": ReportPriority.HIGH.value,
            "status": ReportStatus.RESOLVED.value,
            "resolution": "Full refund provided. Seller banned.",
            "days_ago": 20,
        },
        {
            "content_type": ReportCategory.CHANNELS.value,
            "content_id": "channel-msg-202",
            "content_title": "Spam in Jobs Channel",
            "reason": ReportReason.SPAM.value,
            "description": "Posting MLM recruitment messages.",
            "priority": ReportPriority.LOW.value,
            "status": ReportStatus.DISMISSED.value,
            "resolution": "Content was borderline. Warning issued to user.",
            "days_ago": 12,
        },
    ]

    regular_users = [u for u in users if u.role != Role.ADMIN.value]
    admin_users = [u for u in users if u.role == Role.ADMIN.value]

    if len(regular_users) < 2:
        print("* Not enough regular users for report seeding")
        return []

    for template in report_templates:
        reporter = random.choice(regular_users)
        reported = random.choice([u for u in regular_users if u.id != reporter.id])

        created_at = now - timedelta(days=template.get("days_ago", 0))
        status = template.get("status", ReportStatus.PENDING.value)

        report = Report(
            reported_by_id=reporter.id,
            reported_user_id=reported.id,
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

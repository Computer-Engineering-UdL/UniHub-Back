from datetime import timedelta
from typing import List

from sqlalchemy.orm import Session

from app.domains.channel import ChannelRepository
from app.literals.channels import ChannelCategory, ChannelRole
from app.literals.users import Role
from app.models import Channel, User


def seed_channels(db: Session, users: List[User]) -> List[Channel]:
    """Create university diffusion channels with memberships."""
    repo = ChannelRepository(db)

    channels_data = [
        {
            "name": "📢 Campus Announcements",
            "description": "Official university announcements, events, and important notices",
            "channel_type": "public",
            "category": ChannelCategory.GENERAL,
        },
        {
            "name": "🏠 Housing & Accommodation",
            "description": "Room rentals, roommate search, housing tips and accommodation offers",
            "channel_type": "public",
            "category": ChannelCategory.GENERAL,
        },
        {
            "name": "📚 Study Resources",
            "description": "Share notes, study materials, textbooks, and academic resources",
            "channel_type": "public",
            "category": ChannelCategory.SCIENCES,
        },
        {
            "name": "💼 Jobs & Internships",
            "description": "Job offers, internship opportunities, and career advice for students",
            "channel_type": "public",
            "category": ChannelCategory.BUSINESS,
        },
        {
            "name": "🎉 Events & Activities",
            "description": "Campus events, parties, cultural activities, and social gatherings",
            "channel_type": "public",
            "category": ChannelCategory.GENERAL,
        },
        {
            "name": "🛍️ Buy & Sell",
            "description": "Marketplace for students: books, furniture, electronics, and more",
            "channel_type": "public",
            "category": ChannelCategory.BUSINESS,
        },
        {
            "name": "🏋️ Sports & Wellness",
            "description": "Sports teams, gym buddies, wellness activities, and fitness events",
            "channel_type": "public",
            "category": ChannelCategory.GENERAL,
        },
        {
            "name": "🎨 Arts & Culture",
            "description": "Art exhibitions, theater, music, cinema, and cultural initiatives",
            "channel_type": "public",
            "category": ChannelCategory.ARTS,
        },
        {
            "name": "🌍 International Students",
            "description": "Support and information for international students and exchange programs",
            "channel_type": "public",
            "category": ChannelCategory.GENERAL,
        },
        {
            "name": "💻 Tech & Innovation",
            "description": "Hackathons, tech talks, programming workshops, and innovation projects",
            "channel_type": "public",
            "category": ChannelCategory.ENGINEERING,
        },
        {
            "name": "🍕 Food & Restaurants",
            "description": "Restaurant recommendations, food deals, recipes, and dining tips",
            "channel_type": "public",
            "category": ChannelCategory.GENERAL,
        },
        {
            "name": "🚗 Ride Sharing",
            "description": "Share rides, carpooling for commutes, weekend trips, and travel",
            "channel_type": "public",
            "category": ChannelCategory.GENERAL,
        },
        {
            "name": "🔬 Research & Projects",
            "description": "Research opportunities, academic projects, and collaboration calls",
            "channel_type": "public",
            "category": ChannelCategory.SCIENCES,
        },
        {
            "name": "🌱 Sustainability",
            "description": "Environmental initiatives, recycling, sustainable living, and eco-projects",
            "channel_type": "public",
            "category": ChannelCategory.SCIENCES,
        },
        {
            "name": "🎓 Alumni Network",
            "description": "Connect with alumni, mentorship opportunities, and career networking",
            "channel_type": "public",
            "category": ChannelCategory.GENERAL,
        },
    ]

    created_channels = []

    for channel_data in channels_data:
        existing = repo.get_by_id(db.query(Channel).filter_by(name=channel_data["name"]).first())
        if existing:
            created_channels.append(existing)
            continue

        channel = repo.create(channel_data)
        created_channels.append(channel)

    if len(users) < 3:
        return created_channels

    admin_users = [u for u in users if u.role == Role.ADMIN]
    if not admin_users:
        return created_channels

    regular_users = [u for u in users if u.role != Role.ADMIN][:8]

    for idx, channel in enumerate(created_channels):
        primary_admin = admin_users[idx % len(admin_users)]
        repo.add_member(channel.id, primary_admin.id, ChannelRole.ADMIN)

        if len(admin_users) > 1:
            secondary_admin = admin_users[(idx + 1) % len(admin_users)]
            if secondary_admin.id != primary_admin.id:
                repo.add_member(channel.id, secondary_admin.id, ChannelRole.ADMIN)

        for user in regular_users:
            repo.add_member(channel.id, user.id, ChannelRole.USER)

    if len(created_channels) >= 6 and len(regular_users) >= 1:
        repo.ban_member(
            created_channels[5].id,
            regular_users[0].id,
            "Repeated spam postings in marketplace",
            timedelta(days=14),
            admin_users[0].id,
        )

    print(f"  → {len(created_channels)} channels created")
    return created_channels

from datetime import timedelta
from typing import List

from sqlalchemy.orm import Session

from app.literals.channels import ChannelRole
from app.literals.users import Role
from app.models import Channel, ChannelBan, ChannelMember, User


def seed_channels(db: Session, users: List[User]) -> List[Channel]:
    """Create university diffusion channels with memberships."""

    channels_data = [
        {
            "name": "📢 Campus Announcements",
            "description": "Official university announcements, events, and important notices",
            "channel_type": "public",
            "channel_logo": "https://api.example.com/channels/announcements.jpg",
        },
        {
            "name": "🏠 Housing & Accommodation",
            "description": "Room rentals, roommate search, housing tips and accommodation offers",
            "channel_type": "public",
            "channel_logo": "https://api.example.com/channels/housing.jpg",
        },
        {
            "name": "📚 Study Resources",
            "description": "Share notes, study materials, textbooks, and academic resources",
            "channel_type": "public",
            "channel_logo": None,
        },
        {
            "name": "💼 Jobs & Internships",
            "description": "Job offers, internship opportunities, and career advice for students",
            "channel_type": "public",
            "channel_logo": "https://api.example.com/channels/jobs.jpg",
        },
        {
            "name": "🎉 Events & Activities",
            "description": "Campus events, parties, cultural activities, and social gatherings",
            "channel_type": "public",
            "channel_logo": None,
        },
        {
            "name": "🛍️ Buy & Sell",
            "description": "Marketplace for students: books, furniture, electronics, and more",
            "channel_type": "public",
            "channel_logo": "https://api.example.com/channels/marketplace.jpg",
        },
        {
            "name": "🏋️ Sports & Wellness",
            "description": "Sports teams, gym buddies, wellness activities, and fitness events",
            "channel_type": "public",
            "channel_logo": None,
        },
        {
            "name": "🎨 Arts & Culture",
            "description": "Art exhibitions, theater, music, cinema, and cultural initiatives",
            "channel_type": "public",
            "channel_logo": None,
        },
        {
            "name": "🌍 International Students",
            "description": "Support and information for international students and exchange programs",
            "channel_type": "public",
            "channel_logo": "https://api.example.com/channels/international.jpg",
        },
        {
            "name": "💻 Tech & Innovation",
            "description": "Hackathons, tech talks, programming workshops, and innovation projects",
            "channel_type": "public",
            "channel_logo": None,
        },
        {
            "name": "🍕 Food & Restaurants",
            "description": "Restaurant recommendations, food deals, recipes, and dining tips",
            "channel_type": "public",
            "channel_logo": None,
        },
        {
            "name": "🚗 Ride Sharing",
            "description": "Share rides, carpooling for commutes, weekend trips, and travel",
            "channel_type": "public",
            "channel_logo": None,
        },
        {
            "name": "🔬 Research & Projects",
            "description": "Research opportunities, academic projects, and collaboration calls",
            "channel_type": "public",
            "channel_logo": None,
        },
        {
            "name": "🌱 Sustainability",
            "description": "Environmental initiatives, recycling, sustainable living, and eco-projects",
            "channel_type": "public",
            "channel_logo": "https://api.example.com/channels/sustainability.jpg",
        },
        {
            "name": "🎓 Alumni Network",
            "description": "Connect with alumni, mentorship opportunities, and career networking",
            "channel_type": "public",
            "channel_logo": None,
        },
    ]

    created_channels = []

    for channel_data in channels_data:
        existing = db.query(Channel).filter_by(name=channel_data["name"]).first()
        if existing:
            created_channels.append(existing)
            continue

        channel = Channel(**channel_data)
        db.add(channel)
        db.flush()
        created_channels.append(channel)

    if len(users) < 3:
        print("* Not enough users to seed channel memberships")
        return created_channels

    admin_users = [u for u in users if u.role == Role.ADMIN]
    if not admin_users:
        print("* No admin users found for channel administration")
        return created_channels

    regular_users = [u for u in users if u.role != Role.ADMIN][:8]

    memberships = []

    for idx, channel in enumerate(created_channels):
        primary_admin = admin_users[idx % len(admin_users)]
        memberships.append(ChannelMember(channel_id=channel.id, user_id=primary_admin.id, role=ChannelRole.ADMIN))

        if len(admin_users) > 1:
            secondary_admin = admin_users[(idx + 1) % len(admin_users)]
            if secondary_admin.id != primary_admin.id:
                memberships.append(
                    ChannelMember(
                        channel_id=channel.id,
                        user_id=secondary_admin.id,
                        role=ChannelRole.ADMIN,
                    )
                )

        for user in regular_users:
            memberships.append(ChannelMember(channel_id=channel.id, user_id=user.id, role=ChannelRole.USER))

    for membership in memberships:
        existing = (
            db.query(ChannelMember).filter_by(channel_id=membership.channel_id, user_id=membership.user_id).first()
        )
        if not existing:
            db.add(membership)

    db.flush()

    if len(created_channels) >= 6 and len(regular_users) >= 1:
        _seed_sample_ban(db, created_channels[5], regular_users[0], admin_users[0])

    print(f"* {len(created_channels)} university diffusion channels created")
    print(f"* {len(memberships)} channel memberships created")
    return created_channels


def _seed_sample_ban(db: Session, channel: Channel, banned_user: User, admin: User) -> None:
    """Create a sample ban (e.g., spam in marketplace)."""

    existing_ban = db.query(ChannelBan).filter_by(channel_id=channel.id, user_id=banned_user.id, active=True).first()

    if not existing_ban:
        membership = db.query(ChannelMember).filter_by(channel_id=channel.id, user_id=banned_user.id).first()

        if membership:
            membership.is_banned = True

        ban = ChannelBan(
            channel_id=channel.id,
            user_id=banned_user.id,
            motive="Repeated spam postings in marketplace",
            duration=timedelta(days=14),
            active=True,
            banned_by=admin.id,
        )
        db.add(ban)
        db.flush()

from datetime import timedelta
from typing import List

from sqlalchemy.orm import Session

from app.literals.channels import ChannelRole
from app.models import Channel, ChannelBan, ChannelMember, ChannelUnban, User


def seed_channels(db: Session, users: List[User]) -> None:
    """Create sample channels with memberships, bans, and unbans."""

    channels_data = [
        {
            "name": "General Chat",
            "description": "Main channel for general discussions",
            "channel_type": "public",
            "channel_logo": "https://api.example.com/channels/general.jpg",
        },
        {
            "name": "Study Group - CS",
            "description": "Computer Science study sessions and help",
            "channel_type": "public",
            "channel_logo": None,
        },
        {
            "name": "Gaming Lounge",
            "description": "Discuss games, organize sessions, have fun!",
            "channel_type": "public",
            "channel_logo": "https://api.example.com/channels/gaming.jpg",
        },
        {
            "name": "Private Admins",
            "description": "Admin-only private channel",
            "channel_type": "private",
            "channel_logo": None,
        },
        {
            "name": "Sports & Fitness",
            "description": "Workout plans, sports events, and health tips",
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

    if len(users) < 3 or len(created_channels) < 5:
        return

    admin_user, test_user1, test_user2 = users[0], users[1], users[2]

    memberships = [
        # General Chat - all users
        ChannelMember(channel_id=created_channels[0].id, user_id=admin_user.id, role=ChannelRole.ADMIN),
        ChannelMember(channel_id=created_channels[0].id, user_id=test_user1.id, role=ChannelRole.USER),
        ChannelMember(channel_id=created_channels[0].id, user_id=test_user2.id, role=ChannelRole.MODERATOR),
        # Study Group
        ChannelMember(channel_id=created_channels[1].id, user_id=admin_user.id, role=ChannelRole.ADMIN),
        ChannelMember(channel_id=created_channels[1].id, user_id=test_user1.id, role=ChannelRole.USER),
        # Gaming Lounge
        ChannelMember(channel_id=created_channels[2].id, user_id=test_user1.id, role=ChannelRole.ADMIN),
        ChannelMember(channel_id=created_channels[2].id, user_id=test_user2.id, role=ChannelRole.USER),
        # Private Admins
        ChannelMember(channel_id=created_channels[3].id, user_id=admin_user.id, role=ChannelRole.ADMIN),
        ChannelMember(channel_id=created_channels[3].id, user_id=test_user2.id, role=ChannelRole.MODERATOR),
        # Sports & Fitness
        ChannelMember(channel_id=created_channels[4].id, user_id=admin_user.id, role=ChannelRole.ADMIN),
        ChannelMember(channel_id=created_channels[4].id, user_id=test_user1.id, role=ChannelRole.USER),
        ChannelMember(channel_id=created_channels[4].id, user_id=test_user2.id, role=ChannelRole.USER),
    ]

    for membership in memberships:
        existing = (
            db.query(ChannelMember).filter_by(channel_id=membership.channel_id, user_id=membership.user_id).first()
        )
        if not existing:
            db.add(membership)

    db.flush()

    _seed_bans(db, created_channels, admin_user, test_user1)

    print("* Channels, memberships, bans, and unbans created")


def _seed_bans(db: Session, channels: List[Channel], admin_user: User, test_user1: User) -> None:
    """Create sample bans and unbans."""

    existing_ban = db.query(ChannelBan).filter_by(channel_id=channels[0].id, user_id=test_user1.id).first()

    if not existing_ban:
        old_ban = ChannelBan(
            channel_id=channels[0].id,
            user_id=test_user1.id,
            motive="Spam posting",
            duration=timedelta(days=7),
            active=False,
            banned_by=admin_user.id,
        )
        db.add(old_ban)

        unban = ChannelUnban(
            channel_id=channels[0].id,
            user_id=test_user1.id,
            motive="Appeal accepted, warned",
            unbanned_by=admin_user.id,
        )
        db.add(unban)

    existing_active_ban = (
        db.query(ChannelBan).filter_by(channel_id=channels[4].id, user_id=test_user1.id, active=True).first()
    )

    if not existing_active_ban:
        membership = db.query(ChannelMember).filter_by(channel_id=channels[4].id, user_id=test_user1.id).first()

        if membership:
            membership.is_banned = True

        active_ban = ChannelBan(
            channel_id=channels[4].id,
            user_id=test_user1.id,
            motive="Inappropriate behavior",
            duration=timedelta(days=30),
            active=True,
            banned_by=admin_user.id,
        )
        db.add(active_ban)

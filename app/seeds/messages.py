from datetime import datetime, timedelta
from typing import List

from sqlalchemy.orm import Session

from app.literals.channels import ChannelRole
from app.literals.users import Role
from app.models import Channel, ChannelMember, Message, User


def seed_messages(db: Session, users: List[User], channels: List[Channel]) -> List[Message]:
    """Create sample diffusion messages in university channels."""

    if len(users) < 3 or len(channels) < 3:
        print("* Skipping message seeding - not enough users or channels")
        return []

    all_created_messages = []

    def is_channel_admin(channel_id, user_id):
        """Check if user is site admin OR channel admin (only these can post)."""
        db_user = db.query(User).filter(User.id == user_id).one_or_none()
        if db_user is None:
            return False

        if db_user.role == Role.ADMIN:
            return True

        db_member = db.query(ChannelMember).filter_by(channel_id=channel_id, user_id=user_id).first()
        return db_member is not None and db_member.role == ChannelRole.ADMIN

    def get_channel_by_name(name: str):
        """Helper to find channel by name."""
        for ch in channels:
            if name in ch.name:
                return ch
        return None

    def create_message(channel, user, content, days_ago=0, hours_ago=0, is_edited=False):
        """Helper to create a message if user is admin."""
        if not is_channel_admin(channel.id, user.id):
            return None

        existing = db.query(Message).filter_by(channel_id=channel.id, content=content).first()

        if existing:
            return None

        created_at = datetime.now() - timedelta(days=days_ago, hours=hours_ago)
        updated_at = created_at + timedelta(minutes=15) if is_edited else None

        message = Message(
            channel_id=channel.id,
            user_id=user.id,
            content=content,
            created_at=created_at,
            is_edited=is_edited,
            updated_at=updated_at,
        )
        db.add(message)
        db.flush()
        return message

    admin_users = [u for u in users if u.role == Role.ADMIN]
    if not admin_users:
        print("* No admin users found - cannot create messages")
        return []

    admin1 = admin_users[0]
    admin2 = admin_users[1] if len(admin_users) > 1 else admin1

    campus = get_channel_by_name("Campus Announcements")
    if campus:
        msgs = [
            (
                "🎓 Important: Final exam schedule now available on the student portal. Check your dates and rooms!",
                7,
                0,
            ),
            (
                "📅 University will be closed next Monday for a public holiday. Libraries open with reduced hours.",
                6,
                0,
            ),
            (
                "🏛️ New semester registration opens this Friday at 9 AM. Don't miss the early bird discounts!",
                5,
                0,
            ),
            ("⚠️ Maintenance work in Building C next week. Some classrooms will be relocated temporarily.", 4, 0),
            (
                "🎉 Graduation ceremony scheduled for June 15th. Register at the administration office by May 30th.",
                3,
                0,
            ),
        ]
        for content, days, hours in msgs:
            msg = create_message(campus, admin1, content, days, hours)
            if msg:
                all_created_messages.append(msg)

    housing = get_channel_by_name("Housing")
    if housing:
        msgs = [
            (
                "🏠 Single room available near campus! €350/month, utilities included. "
                "Fully furnished. Contact: housing@student.com",
                6,
                0,
            ),
            (
                "👥 Looking for a roommate for a 2-bedroom apartment. €250/person. Great location, 10 min walk to uni!",
                5,
                0,
            ),
            ("🔑 Student residence has 5 spots available for next semester. Applications close this Friday!", 4, 0),
            (
                "💡 Housing fair this Thursday 10 AM - 4 PM at the Student Center. Meet landlords and find your room!",
                3,
                0,
            ),
            ("📋 Reminder: Housing contracts for next year must be signed before March 31st.", 2, 0),
        ]
        for content, days, hours in msgs:
            msg = create_message(housing, admin2, content, days, hours)
            if msg:
                all_created_messages.append(msg)

    study = get_channel_by_name("Study Resources")
    if study:
        msgs = [
            (
                "📖 Complete set of Linear Algebra notes now available in the library digital collection. Free access!",
                8,
                0,
            ),
            ("💾 Data Structures exam preparation materials uploaded to the shared drive. Link in bio.", 6, 0),
            (
                "📝 Free tutoring sessions for Calculus II every Wednesday 5-7 PM in Room 301. Walk-ins welcome!",
                5,
                0,
            ),
            ("🎯 Study group forming for Database Systems final. Meeting tomorrow at the library, 3rd floor.", 3, 0),
            ("📚 University bookstore has 20% off on all textbooks this week only!", 2, 0),
        ]
        for content, days, hours in msgs:
            msg = create_message(study, admin1, content, days, hours)
            if msg:
                all_created_messages.append(msg)

    jobs = get_channel_by_name("Jobs")
    if jobs:
        msgs = [
            (
                "💼 Tech startup looking for Software Engineering interns. Summer 2025. "
                "Apply at: careers@techstartup.com",
                7,
                0,
            ),
            (
                "🏢 Marketing internship opportunity at local agency. Flexible hours, "
                "great for students. DM for details.",
                6,
                0,
            ),
            ("👔 Career fair next Tuesday! 50+ companies attending. Bring your CVs and dress professionally!", 5, 0),
            ("📊 Part-time data analyst position available. Perfect for Economics students. €15/hour, 15h/week.", 4, 0),
            ("🎓 Summer research assistant positions open in the Engineering department. Deadline: April 15th.", 3, 0),
        ]
        for content, days, hours in msgs:
            msg = create_message(jobs, admin1, content, days, hours)
            if msg:
                all_created_messages.append(msg)

    events = get_channel_by_name("Events")
    if events:
        msgs = [
            (
                "🎊 Spring Festival this Saturday at the campus plaza! Live music, food trucks, "
                "and activities all day!",
                5,
                0,
            ),
            ("🎬 Movie night tonight at 8 PM - screening 'The Social Network'. Free popcorn! Auditorium B.", 3, 0),
            ("🎤 Open mic night this Friday at the Student Bar. Sign up at the door. Show your talent!", 4, 0),
            ("🎨 Art exhibition opening tomorrow: 'Student Perspectives'. Reception at 6 PM, Gallery Hall.", 2, 0),
            ("🏃 Campus Fun Run this Sunday 9 AM. Register at the Sports Center. All levels welcome!", 1, 0),
        ]
        for content, days, hours in msgs:
            msg = create_message(events, admin2, content, days, hours)
            if msg:
                all_created_messages.append(msg)

    marketplace = get_channel_by_name("Buy & Sell")
    if marketplace:
        msgs = [
            (
                "📚 Selling: Organic Chemistry textbook, 3rd edition. Like new. €40 (retail €85). "
                "Contact: seller@student.com",
                6,
                0,
            ),
            (
                "💻 MacBook Air 2021 for sale. €650. 8GB RAM, 256GB SSD. Excellent condition, includes case!",
                5,
                0,
            ),
            ("🚲 Bike for sale - perfect for campus commute. €80. Recently serviced, new lock included.", 4, 0),
            ("🛋️ Moving sale! Desk, chair, lamp, shelf. Everything must go. Great prices. DM for photos.", 3, 0),
            ("📱 iPhone chargers, adapters, and accessories. Various prices. Meet at the library.", 2, 0),
        ]
        for content, days, hours in msgs:
            msg = create_message(marketplace, admin1, content, days, hours)
            if msg:
                all_created_messages.append(msg)

    sports = get_channel_by_name("Sports")
    if sports:
        msgs = [
            (
                "⚽ Soccer team looking for players! Practice every Tuesday and Thursday 6 PM. "
                "All skill levels welcome!",
                6,
                0,
            ),
            ("🏋️ Gym buddy needed for morning workouts (7 AM). Let's stay motivated together!", 5, 0),
            ("🧘 Free yoga classes starting next week. Mondays and Wednesdays 5 PM at the Sports Center.", 4, 0),
            ("🏀 Basketball tournament sign-ups open! Teams of 5. Tournament starts April 20th.", 3, 0),
            ("🏃 Running club meets every Saturday 8 AM. We do 5-10K routes around campus. Join us!", 2, 0),
        ]
        for content, days, hours in msgs:
            msg = create_message(sports, admin2, content, days, hours)
            if msg:
                all_created_messages.append(msg)

    arts = get_channel_by_name("Arts")
    if arts:
        msgs = [
            ("🎭 Theater club presents 'Hamlet' next weekend. Student tickets €5. Shows Fri-Sun at 8 PM.", 7, 0),
            ("🎵 Jazz band looking for a drummer. Rehearsals Thursdays 7 PM. Some experience required.", 5, 0),
            (
                "📸 Photography exhibition: 'Campus Life'. Submit your photos by Friday. "
                "Winners displayed in main hall.",
                4,
                0,
            ),
            ("🎨 Free painting workshop this Wednesday 4-6 PM. All materials provided. No experience needed!", 3, 0),
            ("🎬 Film club meeting tomorrow! This month: Kubrick retrospective. Room 205, 7 PM.", 2, 0),
        ]
        for content, days, hours in msgs:
            msg = create_message(arts, admin1, content, days, hours)
            if msg:
                all_created_messages.append(msg)

    international = get_channel_by_name("International")
    if international:
        msgs = [
            (
                "✈️ New international students: Welcome orientation session this Friday 10 AM. Free breakfast included!",
                6,
                0,
            ),
            ("🗣️ Language exchange meetup every Thursday 6 PM at Café Central. Practice languages, make friends!", 5, 0),
            (
                "📝 Visa renewal workshop next week. Bring your documents. Immigration expert will answer questions.",
                4,
                0,
            ),
            (
                "🌏 Cultural night this Saturday! Share food, music, and traditions from your country. "
                "Everyone welcome!",
                3,
                0,
            ),
            ("🎓 Erasmus students: Buddy program sign-up now open. Get paired with a local student!", 2, 0),
        ]
        for content, days, hours in msgs:
            msg = create_message(international, admin2, content, days, hours)
            if msg:
                all_created_messages.append(msg)

    tech = get_channel_by_name("Tech")
    if tech:
        msgs = [
            ("💻 Hackathon this weekend! 48 hours of coding, prizes, and pizza. Register at: hackathon.uni.edu", 5, 0),
            ("🤖 AI workshop: Introduction to Machine Learning. This Thursday 6 PM. Bring your laptop!", 4, 0),
            ("🔐 Cybersecurity talk by industry expert. Wednesday 7 PM, Auditorium A. Free entry!", 3, 0),
            ("📱 Mobile app development course starting next month. 6-week program. Limited spots available!", 2, 0),
            ("⚡ Lightning talks: Students present their tech projects. Friday 5 PM. Sign up to present!", 1, 0),
        ]
        for content, days, hours in msgs:
            msg = create_message(tech, admin1, content, days, hours)
            if msg:
                all_created_messages.append(msg)

    food = get_channel_by_name("Food")
    if food:
        msgs = [
            ("🍕 New pizza place near campus offers 20% student discount! Show your ID. They deliver too!", 6, 0),
            ("☕ Café Libris has study special: coffee + pastry for €4. Valid Mon-Fri 8 AM - 12 PM.", 5, 0),
            ("🍜 Best ramen in town? Student poll results: Noodle House wins! Check them out on Main Street.", 4, 0),
            (
                "🥗 Healthy eating workshop + meal prep demo this Sunday 11 AM at the Student Center kitchen.",
                3,
                0,
            ),
            ("🍔 Food truck festival tomorrow at campus! 15 trucks, live music, 12-8 PM. Don't miss it!", 1, 0),
        ]
        for content, days, hours in msgs:
            msg = create_message(food, admin2, content, days, hours)
            if msg:
                all_created_messages.append(msg)

    rideshare = get_channel_by_name("Ride Sharing")
    if rideshare:
        msgs = [
            ("🚗 Driving to Barcelona this Friday afternoon. 3 seats available. Split gas costs. DM me!", 5, 0),
            ("🚙 Weekend trip to the mountains planned. Looking for 2-3 people to share ride. Saturday morning.", 4, 0),
            (
                "🚌 Daily commute from downtown? Let's carpool! Save money and environment. "
                "Morning departures 7:30 AM.",
                3,
                0,
            ),
            ("✈️ Airport ride needed Sunday 6 AM. Anyone heading that direction? Will pay for gas!", 2, 0),
            ("🏖️ Beach trip this Saturday! Car full, but organizing second car if 4+ people interested.", 1, 0),
        ]
        for content, days, hours in msgs:
            msg = create_message(rideshare, admin1, content, days, hours)
            if msg:
                all_created_messages.append(msg)

    recent_msgs = [
        (campus, "🔔 Don't forget: Library extends hours during exam period. Open until midnight!", 0, 6),
        (events, "🎪 Surprise concert tonight at 9 PM! Check social media for the band announcement!", 0, 3),
        (housing, "⚡ URGENT: Room available immediately! Previous tenant left early. Great deal!", 0, 2),
    ]

    for channel, content, days, hours in recent_msgs:
        if channel:
            msg = create_message(channel, admin1, content, days, hours)
            if msg:
                all_created_messages.append(msg)

    db.flush()
    print(f"* {len(all_created_messages)} diffusion messages created across university channels")
    return all_created_messages

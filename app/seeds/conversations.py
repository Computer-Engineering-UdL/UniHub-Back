import datetime
import random
import uuid

from sqlalchemy.orm import Session

from app.literals.users import Role
from app.models import (
    Conversation,
    ConversationMessage,
    HousingOfferTableModel,
    User,
)


def seed_user_conversations(db: Session) -> None:
    """
    Seeds the database with realistic conversations between users.
    Creates conversations between students and sellers regarding housing offers,
    and also general conversations between students.
    """
    students = db.query(User).filter(User.role == Role.BASIC, User.is_active.is_(True)).all()
    sellers = db.query(User).filter(User.role == Role.SELLER, User.is_active.is_(True)).all()
    offers = db.query(HousingOfferTableModel).all()

    if not students or not sellers or not offers:
        print("! Not enough active users or offers to seed conversations. Skipping.")
        return

    all_new_models = []
    now = datetime.datetime.now(datetime.UTC)

    available_offers = list(offers)
    random.shuffle(available_offers)
    num_conversations = min(len(available_offers), len(students), 8)

    for i in range(num_conversations):
        offer = available_offers[i]
        student = random.choice(students)

        seller = db.query(User).filter(User.id == offer.user_id).first()
        if not seller or seller.role != Role.SELLER:
            seller = random.choice(sellers)

        if student.id == seller.id:
            continue

        existing_convo = (
            db.query(Conversation)
            .filter(
                (
                    (Conversation.user1_id == student.id)
                    & (Conversation.user2_id == seller.id)
                    & (Conversation.housing_offer_id == offer.id)
                )
                | (
                    (Conversation.user1_id == seller.id)
                    & (Conversation.user2_id == student.id)
                    & (Conversation.housing_offer_id == offer.id)
                )
            )
            .first()
        )
        if existing_convo:
            continue

        convo_start_time = now - datetime.timedelta(days=random.randint(2, 10), hours=random.randint(1, 23))

        conversation = Conversation(
            id=uuid.uuid4(),
            user1_id=student.id,
            user2_id=seller.id,
            housing_offer_id=offer.id,
            created_at=convo_start_time,
            last_message_at=convo_start_time + datetime.timedelta(minutes=25),
        )
        all_new_models.append(conversation)

        messages_content = [
            (
                student,
                (
                    f"Hi {seller.first_name}, is the {offer.category.name.lower()} "
                    f"advertised as '{offer.title}' still available?"
                ),
            ),
            (
                seller,
                f"Hello {student.first_name}. Yes, it's still available. Are you interested in arranging a viewing?",
            ),
            (
                student,
                f"Yes, definitely! I'm a student at the {student.faculty.university.name}. "
                "When would be a good time to see it?",
            ),
            (seller, "I'm available on Friday afternoon or Saturday morning. Would either of those work for you?"),
            (student, "Friday afternoon works perfectly for me. Shall we say around 4 PM?"),
        ]

        for index, (sender, content) in enumerate(messages_content):
            message = ConversationMessage(
                id=uuid.uuid4(),
                conversation_id=conversation.id,
                sender_id=sender.id,
                content=content.format(student=student),
                created_at=convo_start_time + datetime.timedelta(minutes=index * 5 + random.randint(1, 4)),
                is_read=(index < len(messages_content) - 1),
            )
            all_new_models.append(message)

    num_student_convos = min(len(students) // 2, 4)

    for _ in range(num_student_convos):
        student1, student2 = random.sample(students, 2)

        existing_convo = (
            db.query(Conversation)
            .filter(
                ((Conversation.user1_id == student1.id) & (Conversation.user2_id == student2.id))
                | ((Conversation.user1_id == student2.id) & (Conversation.user2_id == student1.id))
            )
            .first()
        )
        if existing_convo:
            continue

        convo_start_time = now - datetime.timedelta(days=random.randint(1, 5))

        conversation = Conversation(
            id=uuid.uuid4(),
            user1_id=student1.id,
            user2_id=student2.id,
            housing_offer_id=None,
            created_at=convo_start_time,
            last_message_at=convo_start_time + datetime.timedelta(hours=1, minutes=10),
        )
        all_new_models.append(conversation)

        messages_content = [
            (
                student1,
                (
                    f"Hey {student2.first_name}, I saw we're both at {student1.faculty.university.name}. "
                    "Are you also looking for a flat for the next semester?"
                ),
            ),
            (student2, "Hey! Yeah, the search is a bit overwhelming. Have you found anything good yet?"),
            (
                student1,
                (
                    "I've seen a couple of interesting places on here. There's a "
                    "decent-looking 2-bedroom flat in Barcelona that might be worth checking out."
                ),
            ),
            (student2, "Oh cool, do you have a link? Maybe we could even look for a place together to split the cost."),
            (student1, "That's a great idea! Let me find it again and I'll send it over."),
        ]

        for index, (sender, content) in enumerate(messages_content):
            message = ConversationMessage(
                id=uuid.uuid4(),
                conversation_id=conversation.id,
                sender_id=sender.id,
                content=content,
                created_at=convo_start_time + datetime.timedelta(minutes=index * 15 + random.randint(1, 10)),
                is_read=True,
            )
            all_new_models.append(message)

    if not all_new_models:
        print("* No new conversations to add.")
        return

    db.add_all(all_new_models)
    db.flush()

    print("* User conversations seeded successfully.")


def seed_admin_conversations(db: Session) -> None:
    """
    Seeds the database with conversations involving admin users for demo purposes.
    """

    admin_user = db.query(User).filter(User.email == "admin@admin.com").first()
    if not admin_user:
        print("! Primary admin user (admin@admin.com) not found. Skipping admin conversation seed.")
        return

    if (
        db.query(Conversation)
        .filter((Conversation.user1_id == admin_user.id) | (Conversation.user2_id == admin_user.id))
        .first()
    ):
        print("* Admin conversations already seem to exist.")
        return

    students = db.query(User).filter(User.role == Role.BASIC, User.is_active.is_(True)).limit(5).all()
    sellers = db.query(User).filter(User.role == Role.SELLER, User.is_active.is_(True)).limit(5).all()

    if not students and not sellers:
        print("! Not enough active users to seed admin conversations.")
        return

    all_new_models = []
    now = datetime.datetime.now(datetime.UTC)

    unverified_student = db.query(User).filter(User.is_verified.is_(False), User.role == Role.BASIC).first()
    if unverified_student:
        convo_start_time = now - datetime.timedelta(days=5, hours=3)

        conversation1 = Conversation(
            id=uuid.uuid4(),
            user1_id=admin_user.id,
            user2_id=unverified_student.id,
            housing_offer_id=None,
            created_at=convo_start_time,
            last_message_at=convo_start_time + datetime.timedelta(hours=1, minutes=15),
        )
        all_new_models.append(conversation1)

        messages1 = [
            (
                admin_user,
                (
                    f"Welcome to the platform, {unverified_student.first_name}! We're glad to have you here. "
                    "Let me know if you need any help getting started."
                ),
            ),
            (unverified_student, "Thanks! I'm trying to figure everything out. How do I get my account verified?"),
            (
                admin_user,
                (
                    "Great question! You can complete the verification process in your profile settings. "
                    "It's a quick step that helps build trust within the community."
                ),
            ),
            (unverified_student, "Okay, I'll check it out. Thanks for the help!"),
        ]

        for index, (sender, content) in enumerate(messages1):
            msg = ConversationMessage(
                id=uuid.uuid4(),
                conversation_id=conversation1.id,
                sender_id=sender.id,
                content=content,
                created_at=convo_start_time + datetime.timedelta(minutes=index * 20 + random.randint(1, 5)),
                is_read=True,
            )
            all_new_models.append(msg)

    seller_with_offer = db.query(User).join(HousingOfferTableModel).filter(User.role == Role.SELLER).first()
    if seller_with_offer:
        convo_start_time = now - datetime.timedelta(days=2, hours=6)

        conversation2 = Conversation(
            id=uuid.uuid4(),
            user1_id=seller_with_offer.id,
            user2_id=admin_user.id,
            housing_offer_id=seller_with_offer.housing_offers[0].id,
            created_at=convo_start_time,
            last_message_at=convo_start_time + datetime.timedelta(days=1, hours=2),
        )
        all_new_models.append(conversation2)

        messages2 = [
            (
                seller_with_offer,
                "Hi Admin, I'm trying to edit the photos for my listing but I can't find the option. Can you help?",
            ),
            (
                admin_user,
                (
                    f"Hello {seller_with_offer.first_name}. Of course. You can manage your listings from your "
                    "dashboard. Next to each offer, there should be an 'Edit' button which will allow you to "
                    "update photos and other details."
                ),
            ),
            (seller_with_offer, "Found it! I don't know how I missed that. Thank you so much."),
            (admin_user, "You're welcome! Happy to help. Let us know if anything else comes up."),
        ]

        for index, (sender, content) in enumerate(messages2):
            msg = ConversationMessage(
                id=uuid.uuid4(),
                conversation_id=conversation2.id,
                sender_id=sender.id,
                content=content,
                created_at=convo_start_time + datetime.timedelta(minutes=index * 45 + random.randint(1, 10)),
                is_read=(index < len(messages2) - 1),
            )
            all_new_models.append(msg)

    if students:
        active_student = random.choice(students)
        convo_start_time = now - datetime.timedelta(hours=20)

        conversation3 = Conversation(
            id=uuid.uuid4(),
            user1_id=admin_user.id,
            user2_id=active_student.id,
            housing_offer_id=None,
            created_at=convo_start_time,
            last_message_at=convo_start_time + datetime.timedelta(minutes=30),
        )
        all_new_models.append(conversation3)

        messages3 = [
            (
                admin_user,
                (
                    f"Hi {active_student.first_name}, this is a quick check-in from the admin team. We hope "
                    "you're finding the platform useful for your flat search!"
                ),
            ),
            (active_student, "Hey! Yes, it's been great so far. Much easier than other sites I've used."),
            (
                admin_user,
                (
                    "That's fantastic to hear! We're always working on improvements, so feel free "
                    "to share any feedback you might have."
                ),
            ),
        ]

        for index, (sender, content) in enumerate(messages3):
            msg = ConversationMessage(
                id=uuid.uuid4(),
                conversation_id=conversation3.id,
                sender_id=sender.id,
                content=content,
                created_at=convo_start_time + datetime.timedelta(minutes=index * 15 + random.randint(1, 3)),
                is_read=True,
            )
            all_new_models.append(msg)

    if not all_new_models:
        print("* No new admin conversations to add.")
        return

    db.add_all(all_new_models)
    db.flush()

    print("* Admin conversations seeded successfully.")


def seed_conversations(db: Session) -> None:
    """
    Seed the database with conversations for demo purposes.
    """
    if db.query(Conversation).first():
        print("* Conversations already exist.")
        return
    seed_user_conversations(db)
    seed_admin_conversations(db)

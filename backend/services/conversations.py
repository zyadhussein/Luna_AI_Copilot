from sqlalchemy import select
from sqlalchemy.orm import Session

from db_models import (
    ConversationDB,
    ChatMessageDB,
)


def create_conversation(
    db: Session,
    title: str = "New conversation"
):
    conversation = ConversationDB(
        title=title
    )

    db.add(conversation)
    db.commit()
    db.refresh(conversation)

    return conversation


def add_message(
    conversation_id: int,
    role: str,
    content: str,
    db: Session
):
    message = ChatMessageDB(
        conversation_id=conversation_id,
        role=role,
        content=content,
    )

    db.add(message)
    db.commit()
    db.refresh(message)

    return message


def get_conversation_messages(
    conversation_id: int,
    db: Session
):
    statement = (
        select(ChatMessageDB)
        .where(
            ChatMessageDB.conversation_id
            == conversation_id
        )
        .order_by(ChatMessageDB.created_at)
    )

    return list(
        db.scalars(statement).all()
    )


def get_conversations(
    db: Session
):
    statement = (
        select(ConversationDB)
        .order_by(
            ConversationDB.created_at.desc()
        )
    )

    return list(
        db.scalars(statement).all()
    )
from datetime import date, datetime

from sqlalchemy import ForeignKey, String, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import JSONB
from database import Base


class ApartmentDB(Base):
    __tablename__ = "apartments"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    name: Mapped[str] = mapped_column(
        String(100)
    )

    capacity: Mapped[int]

    base_price: Mapped[float]


class BookingDB(Base):
    __tablename__ = "bookings"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True
    )

    apartment_id: Mapped[int] = mapped_column(
        ForeignKey("apartments.id")
    )

    guest_name: Mapped[str] = mapped_column(
        String(100)
    )

    check_in: Mapped[date]

    check_out: Mapped[date]

    guest_count: Mapped[int]

    total_price: Mapped[float]

    status: Mapped[str] = mapped_column(
        String(30),
        default="confirmed"
    )
class AgentInteractionDB(Base):
    __tablename__ = "agent_interactions"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True
    )

    user_message: Mapped[str] = mapped_column(
        String(1000)
    )

    status: Mapped[str] = mapped_column(
        String(50)
    )

    tool_count: Mapped[int] = mapped_column(
        default=0
    )

    latency_seconds: Mapped[float]

    created_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow
    )





class ConversationDB(Base):
    __tablename__ = "conversations"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True
    )

    title: Mapped[str] = mapped_column(
        String(255),
        default="New conversation"
    )
    state: Mapped[dict] = mapped_column(
        JSONB,
        default=dict,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow
    )


class ChatMessageDB(Base):
    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True
    )

    conversation_id: Mapped[int] = mapped_column(
        ForeignKey("conversations.id")
    )

    role: Mapped[str] = mapped_column(
        String(20)
    )

    content: Mapped[str] = mapped_column(
        Text
    )

    created_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow
    )
class PendingActionDB(Base):
    __tablename__ = "pending_actions"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
    )

    conversation_id: Mapped[int] = mapped_column(
        ForeignKey("conversations.id"),
    )

    tool_name: Mapped[str] = mapped_column(
        String(100),
    )

    arguments: Mapped[dict] = mapped_column(
        JSON,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default="pending",
    )

    created_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow,
    )
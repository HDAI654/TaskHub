from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    Enum,
    UniqueConstraint,
    Text,
    Boolean,
)
from src.modules.core.database import Base


class CardModel(Base):
    __tablename__ = "cards"

    id = Column(Integer, primary_key=True, index=True)
    public_id = Column(String(36), unique=True, nullable=False, index=True)
    column_id = Column(
        String,
        ForeignKey("columns.public_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title = Column(String(500), nullable=False, index=True)
    description = Column(Text, nullable=False)
    priority = Column(
        Enum("low", "medium", "high", "urgent", name="priority_enum"), nullable=False
    )
    due_date = Column(DateTime(timezone=True), nullable=False)
    created_by_user_id = Column(String, ForeignKey("users.public_id"))
    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class CardAssigneesModel(Base):
    __tablename__ = "card_assignees"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.public_id", ondelete="CASCADE"))
    card_id = Column(String, ForeignKey("cards.public_id", ondelete="CASCADE"))
    assigned_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    __table_args__ = (UniqueConstraint("user_id", "card_id", name="uq_user_card"),)


class CheckListsModel(Base):
    __tablename__ = "checklists"

    id = Column(Integer, primary_key=True, index=True)
    public_id = Column(String(36), unique=True, nullable=False, index=True)
    title = Column(String(500), nullable=False, index=True)
    card_id = Column(String, ForeignKey("cards.public_id", ondelete="CASCADE"))
    is_checked = Column(Boolean, default=False)


class LabelsModel(Base):
    __tablename__ = "labels"

    id = Column(Integer, primary_key=True, index=True)
    public_id = Column(String(36), unique=True, nullable=False, index=True)
    name = Column(String(50), nullable=False, index=True)


class CardLabels(Base):
    __tablename__ = "card_labels"

    id = Column(Integer, primary_key=True, index=True)
    label_id = Column(String, ForeignKey("labels.public_id"))
    card_id = Column(String, ForeignKey("cards.public_id"))

from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    Enum,
    UniqueConstraint,
)
from src.modules.core.database import Base


class OrgModel(Base):
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True)
    public_id = Column(String(36), unique=True, nullable=False, index=True)
    name = Column(String(50), nullable=False, index=True)
    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self):
        return f"<Organization(public_id='{self.public_id}', name='{self.name}')>"


class OrgMemberModel(Base):
    __tablename__ = "org_members"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.public_id"), nullable=False, index=True)
    organization_id = Column(
        String, ForeignKey("organizations.public_id"), nullable=False, index=True
    )
    role = Column(
        Enum("owner", "admin", "member", "viewer", name="role_enum"), nullable=False
    )
    joined_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    __table_args__ = (
        UniqueConstraint("user_id", "organization_id", name="uq_user_organization"),
    )

    def __repr__(self):
        return f"<OrgMember(user_id={self.user_id}, org_id={self.organization_id}, role='{self.role}')>"

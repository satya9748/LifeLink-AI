from datetime import datetime
from sqlalchemy import String, Integer, DateTime, Boolean, ForeignKey, Enum, Text, Float, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.db.database import Base

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    full_name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(180), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(Enum("admin", "hospital", "blood_bank", "donor", name="user_role"))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class Hospital(Base):
    __tablename__ = "hospitals"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    name: Mapped[str] = mapped_column(String(180))
    address: Mapped[str] = mapped_column(Text)
    city: Mapped[str] = mapped_column(String(100), index=True)
    state: Mapped[str] = mapped_column(String(100))
    phone: Mapped[str] = mapped_column(String(20))

class BloodBank(Base):
    __tablename__ = "blood_banks"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    name: Mapped[str] = mapped_column(String(180))
    license_number: Mapped[str] = mapped_column(String(100), unique=True)
    address: Mapped[str] = mapped_column(Text)
    city: Mapped[str] = mapped_column(String(100), index=True)
    state: Mapped[str] = mapped_column(String(100))
    phone: Mapped[str] = mapped_column(String(20))
    verified: Mapped[bool] = mapped_column(Boolean, default=False)

class Donor(Base):
    __tablename__ = "donors"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    blood_group: Mapped[str] = mapped_column(String(3), index=True)
    city: Mapped[str] = mapped_column(String(100), index=True)
    state: Mapped[str] = mapped_column(String(100))
    phone: Mapped[str] = mapped_column(String(20))
    consent_to_alerts: Mapped[bool] = mapped_column(Boolean, default=False)
    available_for_contact: Mapped[bool] = mapped_column(Boolean, default=False)
    last_donation_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

class BloodUnit(Base):
    __tablename__ = "blood_units"
    id: Mapped[int] = mapped_column(primary_key=True)
    blood_bank_id: Mapped[int] = mapped_column(ForeignKey("blood_banks.id"), index=True)
    unit_code: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    blood_group: Mapped[str] = mapped_column(String(3), index=True)
    component: Mapped[str] = mapped_column(String(40))
    quantity_ml: Mapped[int] = mapped_column(Integer, default=450)
    collection_date: Mapped[datetime] = mapped_column(DateTime)
    expiry_date: Mapped[datetime] = mapped_column(DateTime, index=True)
    screening_status: Mapped[str] = mapped_column(String(30), default="pending")
    status: Mapped[str] = mapped_column(String(30), default="available", index=True)

class BloodRequest(Base):
    __tablename__ = "blood_requests"
    id: Mapped[int] = mapped_column(primary_key=True)
    hospital_id: Mapped[int] = mapped_column(ForeignKey("hospitals.id"), index=True)
    blood_group: Mapped[str] = mapped_column(String(3))
    component: Mapped[str] = mapped_column(String(40))
    units_required: Mapped[int] = mapped_column(Integer)
    urgency: Mapped[str] = mapped_column(String(20), default="normal")
    city: Mapped[str] = mapped_column(String(100), index=True)
    clinical_reference: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="open", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class Notification(Base):
    __tablename__ = "notifications"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    title: Mapped[str] = mapped_column(String(180))
    message: Mapped[str] = mapped_column(Text)
    channel: Mapped[str] = mapped_column(String(30), default="in_app")
    status: Mapped[str] = mapped_column(String(30), default="queued")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
class BloodBankResponse(Base):
    __tablename__ = "blood_bank_responses"

    __table_args__ = (
        UniqueConstraint(
            "request_id",
            "blood_bank_id",
            name="uq_request_blood_bank"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    request_id: Mapped[int] = mapped_column(
        ForeignKey("blood_requests.id"), index=True
    )

    blood_bank_id: Mapped[int] = mapped_column(
        ForeignKey("blood_banks.id"), index=True
    )

    response_status: Mapped[str] = mapped_column(
        String(30), default="pending"
    )

    units_offered: Mapped[int] = mapped_column(
        Integer, default=0
    )

    response_message: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )

    responded_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )
# ==============================
# GMAIL ACCOUNT CONNECTION
# ==============================

class GmailConnection(Base):
    __tablename__ = "gmail_connections"

    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        unique=True,
        index=True
    )

    gmail_email: Mapped[str] = mapped_column(String(180))

    encrypted_refresh_token: Mapped[str] = mapped_column(Text)

    scopes: Mapped[str] = mapped_column(Text)

    connected_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

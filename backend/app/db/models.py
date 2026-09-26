import uuid
from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    JSON,
    String,
    Text,
    Uuid,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


# ══════════════════════════════════════════════════════════
# ১. ইউজার
# ══════════════════════════════════════════════════════════
class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    clerk_id: Mapped[str] = mapped_column(
        String(128), unique=True, index=True, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # ── নোটিফিকেশন ──
    telegram_chat_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    notify_enabled: Mapped[bool] = mapped_column(Boolean, default=True)

    profile: Mapped["CandidateProfile"] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    applications: Mapped[list["Application"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class CandidateProfile(Base):
    __tablename__ = "candidate_profiles"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True
    )
    parsed_data: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    user: Mapped["User"] = relationship(back_populates="profile")


# ══════════════════════════════════════════════════════════
# ২. জব — সব সোর্সের সার্কুলার এক জায়গায়
# ══════════════════════════════════════════════════════════
class Job(Base):
    """
    id হিসেবে JobItem-এর ১২ অক্ষরের হ্যাশ ব্যবহার হয়।
    একই সার্কুলার দশবার ফেচ হলেও একটাই সারি থাকবে।

    days_left বা urgency এখানে রাখা হয় না — ওগুলো প্রতিদিন বদলায়,
    তাই পড়ার সময় deadline থেকে হিসাব করা হয়।
    """

    __tablename__ = "jobs"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)

    title: Mapped[str] = mapped_column(String(512), nullable=False)
    company: Mapped[str] = mapped_column(String(512), default="")
    location: Mapped[str] = mapped_column(String(256), default="")
    district: Mapped[str] = mapped_column(String(128), default="", index=True)
    is_remote: Mapped[bool] = mapped_column(Boolean, default=False, index=True)

    job_type: Mapped[str] = mapped_column(String(64), default="Local")
    source: Mapped[str] = mapped_column(String(64), default="", index=True)
    url: Mapped[str] = mapped_column(Text, default="")

    description: Mapped[str] = mapped_column(Text, default="")
    salary: Mapped[str] = mapped_column(String(256), default="")
    posted_date: Mapped[str] = mapped_column(String(64), default="")

    sectors: Mapped[list] = mapped_column(JSON, default=list)
    job_function: Mapped[str] = mapped_column(String(32), default="general", index=True)
    tags: Mapped[list] = mapped_column(JSON, default=list)

    deadline: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)

    first_seen_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, index=True
    )
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)

    applications: Mapped[list["Application"]] = relationship(back_populates="job")

    __table_args__ = (
        Index("ix_jobs_active_deadline", "is_active", "deadline"),
        Index("ix_jobs_source_first_seen", "source", "first_seen_at"),
    )


# ══════════════════════════════════════════════════════════
# ৩. আবেদন ট্র্যাকার
# ══════════════════════════════════════════════════════════
STATUS_SAVED = "SAVED"
STATUS_APPLIED = "APPLIED"
STATUS_EXAM = "EXAM"
STATUS_INTERVIEW = "INTERVIEW"
STATUS_OFFER = "OFFER"
STATUS_REJECTED = "REJECTED"


class Application(Base):
    """
    job_snapshot রাখা হয় ইচ্ছাকৃতভাবে — সার্কুলার সাইট থেকে মুছে গেলেও
    ইউজার যেন দেখতে পায় সে কোথায় আবেদন করেছিল।
    """

    __tablename__ = "applications"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    job_id: Mapped[str] = mapped_column(
        ForeignKey("jobs.id", ondelete="CASCADE"), index=True
    )

    status: Mapped[str] = mapped_column(String(32), default=STATUS_SAVED, index=True)

    # ── সরকারি চাকরির জন্য অপরিহার্য ──
    tracking_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    fee_paid: Mapped[bool] = mapped_column(Boolean, default=False)
    admit_downloaded: Mapped[bool] = mapped_column(Boolean, default=False)
    exam_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    notes: Mapped[str] = mapped_column(Text, default="")
    job_snapshot: Mapped[dict] = mapped_column(JSON, default=dict)

    applied_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    user: Mapped["User"] = relationship(back_populates="applications")
    job: Mapped["Job"] = relationship(back_populates="applications")

    __table_args__ = (
        Index("ix_applications_user_status", "user_id", "status"),
    )


# ══════════════════════════════════════════════════════════
# ৪. সেভ করা সার্চ — অ্যালার্টের ভিত্তি
# ══════════════════════════════════════════════════════════
class SavedSearch(Base):
    __tablename__ = "saved_searches"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )

    name: Mapped[str] = mapped_column(String(128), default="আমার সার্চ")
    filters: Mapped[dict] = mapped_column(JSON, default=dict)

    notify_telegram: Mapped[bool] = mapped_column(Boolean, default=True)
    notify_email: Mapped[bool] = mapped_column(Boolean, default=False)

    last_notified_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


# ══════════════════════════════════════════════════════════
# ৫. পাঠানো নোটিফিকেশন — একই জিনিস দুইবার না পাঠাতে
# ══════════════════════════════════════════════════════════
class NotificationLog(Base):
    __tablename__ = "notification_logs"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    job_id: Mapped[str | None] = mapped_column(String(32), nullable=True)

    channel: Mapped[str] = mapped_column(String(32), default="telegram")
    kind: Mapped[str] = mapped_column(String(32), default="new_match")
    sent_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_notif_user_job_kind", "user_id", "job_id", "kind"),
    )
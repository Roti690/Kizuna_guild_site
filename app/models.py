from sqlalchemy import String, Integer, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from .db import Base

class Member(Base):
    __tablename__ = "members"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    role: Mapped[str] = mapped_column(String(40), default="Member")

    # Status for the two most recent weeks (week1 = last week, week2 = week before)
    week1_status: Mapped[str] = mapped_column(String(20), default="active")
    week2_status: Mapped[str] = mapped_column(String(20), default="active")

    note: Mapped[str | None] = mapped_column(String(140), nullable=True)

class Post(Base):
    __tablename__ = "posts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(120))
    body: Mapped[str] = mapped_column(Text)

class EventConfig(Base):
    __tablename__ = "event_config"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # store times as strings (easy manual editing)
    breaking_sat: Mapped[str] = mapped_column(String(40), default="18:30-19:30")
    breaking_sun: Mapped[str] = mapped_column(String(40), default="16:30-17:30")

    skill_sat: Mapped[str] = mapped_column(String(40), default="16:30-17:30")
    skill_sun: Mapped[str] = mapped_column(String(40), default="16:30-17:30")

    party_daily: Mapped[str] = mapped_column(String(40), default="19:00")

    raids_sat: Mapped[str] = mapped_column(String(40), default="20:00")
    raids_sun: Mapped[str] = mapped_column(String(40), default="20:00")

class Guide(Base):
    __tablename__ = "guides"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    slug: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(140))
    category: Mapped[str] = mapped_column(String(20), default="general")  # general | build
    summary: Mapped[str] = mapped_column(String(220), default="")
    cover_image: Mapped[str | None] = mapped_column(String(200), nullable=True)  # "/static/uploads/.."
    content_md: Mapped[str] = mapped_column(Text, default="")

class GuideImage(Base):
    __tablename__ = "guide_images"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    guide_id: Mapped[int] = mapped_column(ForeignKey("guides.id", ondelete="CASCADE"))
    path: Mapped[str] = mapped_column(String(200))  # /static/uploads/...

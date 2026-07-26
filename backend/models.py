from sqlalchemy import (
    Boolean,
    Column,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)

from backend.database import Base


class Schedule(Base):
    __tablename__ = "schedules"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    date = Column(
        String,
        index=True,
        nullable=False,
    )

    time = Column(
        String,
        nullable=False,
    )

    text = Column(
        String,
        nullable=False,
    )

    completed = Column(
        Boolean,
        default=False,
        nullable=False,
    )

    category = Column(
        String,
        default="daily",
        nullable=False,
    )

    important = Column(
        Boolean,
        default=False,
        nullable=False,
    )

    repeat_type = Column(
        String,
        default="none",
        nullable=False,
    )

    repeat_until = Column(
        String,
        nullable=True,
    )


class ScheduleOccurrence(Base):
    __tablename__ = "schedule_occurrences"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    schedule_id = Column(
        Integer,
        ForeignKey(
            "schedules.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    date = Column(
        String,
        nullable=False,
        index=True,
    )

    completed = Column(
        Boolean,
        default=False,
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint(
            "schedule_id",
            "date",
            name="uq_schedule_occurrence",
        ),
    )


class Todo(Base):
    __tablename__ = "todos"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    date = Column(
        String,
        index=True,
        nullable=False,
    )

    text = Column(
        String,
        nullable=False,
    )

    completed = Column(
        Boolean,
        default=False,
        nullable=False,
    )


class DailyNote(Base):
    __tablename__ = "daily_notes"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    date = Column(
        String,
        unique=True,
        index=True,
        nullable=False,
    )

    text = Column(
        Text,
        default="",
    )
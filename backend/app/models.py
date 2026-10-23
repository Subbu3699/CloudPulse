
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class MonitoredAPI(Base):
    __tablename__ = "monitored_apis"

    id = Integer().with_variant(Integer, "sqlite")

    # Primary identifier
    id = __import__("sqlalchemy").Column(
        Integer, primary_key=True, index=True
    )
    name = __import__("sqlalchemy").Column(String(100), nullable=False)
    url = __import__("sqlalchemy").Column(String(2048), nullable=False)
    method = __import__("sqlalchemy").Column(
        String(10), nullable=False, default="GET"
    )
    check_interval_seconds = __import__("sqlalchemy").Column(
        Integer, nullable=False, default=60
    )
    timeout_seconds = __import__("sqlalchemy").Column(
        Integer, nullable=False, default=10
    )
    is_active = __import__("sqlalchemy").Column(
        Boolean, nullable=False, default=True
    )
    created_at = __import__("sqlalchemy").Column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )

    checks = relationship(
        "MonitoringCheck",
        back_populates="api",
        cascade="all, delete-orphan",
    )
    incidents = relationship(
        "Incident",
        back_populates="api",
        cascade="all, delete-orphan",
    )


class MonitoringCheck(Base):
    __tablename__ = "monitoring_checks"

    id = __import__("sqlalchemy").Column(
        Integer, primary_key=True, index=True
    )
    api_id = __import__("sqlalchemy").Column(
        Integer,
        ForeignKey("monitored_apis.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status_code = __import__("sqlalchemy").Column(Integer, nullable=True)
    response_time_ms = __import__("sqlalchemy").Column(Float, nullable=True)
    is_success = __import__("sqlalchemy").Column(
        Boolean, nullable=False, default=False
    )
    error_message = __import__("sqlalchemy").Column(Text, nullable=True)
    checked_at = __import__("sqlalchemy").Column(
        DateTime(timezone=True), nullable=False, default=utc_now, index=True
    )

    api = relationship("MonitoredAPI", back_populates="checks")


class Incident(Base):
    __tablename__ = "incidents"

    id = __import__("sqlalchemy").Column(
        Integer, primary_key=True, index=True
    )
    api_id = __import__("sqlalchemy").Column(
        Integer,
        ForeignKey("monitored_apis.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title = __import__("sqlalchemy").Column(String(200), nullable=False)
    description = __import__("sqlalchemy").Column(Text, nullable=True)
    severity = __import__("sqlalchemy").Column(
        String(20), nullable=False, default="major"
    )
    status = __import__("sqlalchemy").Column(
        String(20), nullable=False, default="open"
    )
    started_at = __import__("sqlalchemy").Column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )
    resolved_at = __import__("sqlalchemy").Column(
        DateTime(timezone=True), nullable=True
    )

    api = relationship("MonitoredAPI", back_populates="incidents")

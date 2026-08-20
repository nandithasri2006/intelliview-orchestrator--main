"""Risk score override audit ORM model."""

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String

from database.models._base import Base, utcnow


class RiskScoreOverrideAudit(Base):
    """
    Audit record for manual interview risk score overrides.

    Stores the old and new risk scores, who performed the override,
    and when the override occurred.
    """

    __tablename__ = "risk_score_override_audit"

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    session_id = Column(
        String(255),
        ForeignKey("interview_sessions.session_id"),
        nullable=False,
        index=True,
    )

    old_score = Column(
        Float,
        nullable=False,
    )

    new_score = Column(
        Float,
        nullable=False,
    )

    overridden_by = Column(
        String(255),
        nullable=False,
    )

    timestamp = Column(
        DateTime(timezone=True),
        nullable=False,
        default=utcnow,
    )

    def __repr__(self):
        return (
            f"<RiskScoreOverrideAudit("
            f"id={self.id}, "
            f"session_id='{self.session_id}', "
            f"old_score={self.old_score}, "
            f"new_score={self.new_score}, "
            f"overridden_by='{self.overridden_by}')>"
        )
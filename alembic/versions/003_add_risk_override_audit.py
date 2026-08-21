"""create risk score override audit table.

Revision ID: 003_add_risk_override_audit
Revises: 002_add_llm_usage
Create Date: 2026-08-20
"""

import sqlalchemy as sa

from alembic import op

revision = "003_add_risk_override_audit"
down_revision = "002_add_llm_usage"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "risk_score_override_audit",
        sa.Column(
            "id",
            sa.Integer(),
            primary_key=True,
            autoincrement=True,
        ),
        sa.Column(
            "session_id",
            sa.String(255),
            sa.ForeignKey("interview_sessions.session_id"),
            nullable=False,
        ),
        sa.Column(
            "old_score",
            sa.Float(),
            nullable=False,
        ),
        sa.Column(
            "new_score",
            sa.Float(),
            nullable=False,
        ),
        sa.Column(
            "overridden_by",
            sa.String(255),
            nullable=False,
        ),
        sa.Column(
            "timestamp",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
    )

    op.create_index(
        "ix_risk_score_override_audit_session_id",
        "risk_score_override_audit",
        ["session_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_risk_score_override_audit_session_id",
        table_name="risk_score_override_audit",
    )

    op.drop_table("risk_score_override_audit")

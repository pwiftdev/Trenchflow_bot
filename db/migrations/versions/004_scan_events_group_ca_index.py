"""Index first-call lookup: group_id + ca ordered by scanned_at.

Revision ID: 004
Revises: 003
"""

from typing import Sequence, Union

from alembic import op

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        "ix_scan_events_group_ca_scanned_at",
        "scan_events",
        ["group_id", "ca", "scanned_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_scan_events_group_ca_scanned_at", table_name="scan_events")

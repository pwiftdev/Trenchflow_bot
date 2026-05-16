"""Store market cap at scan time for since-call PnL.

Revision ID: 002
Revises: 001
Create Date: 2026-05-16

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "scan_events",
        sa.Column("market_cap_usd", sa.Numeric(precision=18, scale=2), nullable=True),
    )
    op.add_column(
        "scan_events",
        sa.Column("price_usd", sa.Numeric(precision=24, scale=12), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("scan_events", "price_usd")
    op.drop_column("scan_events", "market_cap_usd")

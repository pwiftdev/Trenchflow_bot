"""Initial schema: tokens, groups, wallets, tracked_wallets, scan_events, swaps.

Revision ID: 001
Revises:
Create Date: 2026-05-15

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "tokens",
        sa.Column("mint", sa.String(length=44), nullable=False),
        sa.Column("symbol", sa.String(length=32), nullable=True),
        sa.Column("name", sa.String(length=256), nullable=True),
        sa.Column("token_metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("mint"),
    )
    op.create_table(
        "groups",
        sa.Column("group_id", sa.BigInteger(), nullable=False),
        sa.Column("name", sa.String(length=256), nullable=True),
        sa.Column(
            "min_usd_threshold",
            sa.Numeric(precision=18, scale=2),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("group_id"),
    )
    op.create_table(
        "wallets",
        sa.Column("address", sa.String(length=44), nullable=False),
        sa.Column("first_seen", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_seen", sa.DateTime(timezone=True), nullable=True),
        sa.Column("pnl_7d", sa.Numeric(precision=18, scale=2), nullable=True),
        sa.Column("pnl_30d", sa.Numeric(precision=18, scale=2), nullable=True),
        sa.Column("win_rate", sa.Numeric(precision=5, scale=4), nullable=True),
        sa.Column("hit_rate", sa.Numeric(precision=5, scale=4), nullable=True),
        sa.Column("rating_score", sa.Numeric(precision=5, scale=4), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("address"),
    )
    op.create_table(
        "tracked_wallets",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("group_id", sa.BigInteger(), nullable=False),
        sa.Column("wallet_address", sa.String(length=44), nullable=False),
        sa.Column("label", sa.String(length=128), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["group_id"], ["groups.group_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["wallet_address"], ["wallets.address"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("group_id", "wallet_address", name="uq_tracked_wallets_group_wallet"),
    )
    op.create_table(
        "scan_events",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("ca", sa.String(length=44), nullable=False),
        sa.Column("group_id", sa.BigInteger(), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=True),
        sa.Column(
            "scanned_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["group_id"], ["groups.group_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_scan_events_ca_scanned_at", "scan_events", ["ca", "scanned_at"])
    op.create_table(
        "swaps",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("wallet_address", sa.String(length=44), nullable=False),
        sa.Column("mint", sa.String(length=44), nullable=False),
        sa.Column("side", sa.String(length=8), nullable=False),
        sa.Column("token_amount", sa.Numeric(precision=38, scale=18), nullable=True),
        sa.Column("usd_value", sa.Numeric(precision=18, scale=2), nullable=True),
        sa.Column("tx_signature", sa.String(length=88), nullable=False),
        sa.Column("block_time", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["wallet_address"], ["wallets.address"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tx_signature", name="uq_swaps_tx_signature"),
    )
    op.create_index("ix_swaps_wallet_block_time", "swaps", ["wallet_address", "block_time"])


def downgrade() -> None:
    op.drop_index("ix_swaps_wallet_block_time", table_name="swaps")
    op.drop_table("swaps")
    op.drop_index("ix_scan_events_ca_scanned_at", table_name="scan_events")
    op.drop_table("scan_events")
    op.drop_table("tracked_wallets")
    op.drop_table("wallets")
    op.drop_table("groups")
    op.drop_table("tokens")

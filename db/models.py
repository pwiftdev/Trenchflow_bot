from datetime import datetime
from typing import Optional

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Token(Base):
    __tablename__ = "tokens"

    mint: Mapped[str] = mapped_column(String(44), primary_key=True)
    symbol: Mapped[Optional[str]] = mapped_column(String(32))
    name: Mapped[Optional[str]] = mapped_column(String(256))
    token_metadata: Mapped[Optional[dict]] = mapped_column(JSONB)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class Group(Base):
    __tablename__ = "groups"

    group_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[Optional[str]] = mapped_column(String(256))
    min_usd_threshold: Mapped[float] = mapped_column(Numeric(18, 2), default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class Wallet(Base):
    __tablename__ = "wallets"

    address: Mapped[str] = mapped_column(String(44), primary_key=True)
    first_seen: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    last_seen: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    pnl_7d: Mapped[Optional[float]] = mapped_column(Numeric(18, 2))
    pnl_30d: Mapped[Optional[float]] = mapped_column(Numeric(18, 2))
    win_rate: Mapped[Optional[float]] = mapped_column(Numeric(5, 4))
    hit_rate: Mapped[Optional[float]] = mapped_column(Numeric(5, 4))
    rating_score: Mapped[Optional[float]] = mapped_column(Numeric(5, 4))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class TrackedWallet(Base):
    __tablename__ = "tracked_wallets"
    __table_args__ = (
        UniqueConstraint("group_id", "wallet_address", name="uq_tracked_wallets_group_wallet"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    group_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("groups.group_id", ondelete="CASCADE"), nullable=False
    )
    wallet_address: Mapped[str] = mapped_column(
        String(44), ForeignKey("wallets.address", ondelete="CASCADE"), nullable=False
    )
    label: Mapped[Optional[str]] = mapped_column(String(128))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class ScanEvent(Base):
    __tablename__ = "scan_events"
    __table_args__ = (Index("ix_scan_events_ca_scanned_at", "ca", "scanned_at"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ca: Mapped[str] = mapped_column(String(44), nullable=False)
    group_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("groups.group_id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    market_cap_usd: Mapped[Optional[float]] = mapped_column(Numeric(18, 2))
    price_usd: Mapped[Optional[float]] = mapped_column(Numeric(24, 12))
    scanned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class Swap(Base):
    __tablename__ = "swaps"
    __table_args__ = (
        Index("ix_swaps_wallet_block_time", "wallet_address", "block_time"),
        UniqueConstraint("tx_signature", name="uq_swaps_tx_signature"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    wallet_address: Mapped[str] = mapped_column(
        String(44), ForeignKey("wallets.address", ondelete="CASCADE"), nullable=False
    )
    mint: Mapped[str] = mapped_column(String(44), nullable=False)
    side: Mapped[str] = mapped_column(String(8), nullable=False)
    token_amount: Mapped[Optional[float]] = mapped_column(Numeric(38, 18))
    usd_value: Mapped[Optional[float]] = mapped_column(Numeric(18, 2))
    tx_signature: Mapped[str] = mapped_column(String(88), nullable=False)
    block_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from sqlalchemy import func, select, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Group, ScanEvent


@dataclass(frozen=True)
class FirstScanRow:
    user_id: Optional[int]
    scanned_at: datetime
    market_cap_usd: Optional[float]
    price_usd: Optional[float]
    scanner_full_name: Optional[str]
    scanner_username: Optional[str]


async def ping_database(session: AsyncSession) -> bool:
    result = await session.execute(text("SELECT 1"))
    return result.scalar_one() == 1


async def fetch_first_scan_in_chat(
    session: AsyncSession,
    *,
    ca: str,
    group_id: int,
) -> Optional[FirstScanRow]:
    result = await session.execute(
        select(
            ScanEvent.user_id,
            ScanEvent.scanned_at,
            ScanEvent.market_cap_usd,
            ScanEvent.price_usd,
            ScanEvent.scanner_full_name,
            ScanEvent.scanner_username,
        )
        .where(ScanEvent.ca == ca, ScanEvent.group_id == group_id)
        .order_by(ScanEvent.scanned_at.asc())
        .limit(1)
    )
    row = result.first()
    if row is None:
        return None
    return FirstScanRow(
        user_id=row[0],
        scanned_at=row[1],
        market_cap_usd=float(row[2]) if row[2] is not None else None,
        price_usd=float(row[3]) if row[3] is not None else None,
        scanner_full_name=row[4],
        scanner_username=row[5],
    )


async def count_distinct_groups_for_ca(
    session: AsyncSession,
    *,
    ca: str,
    since: datetime,
) -> int:
    result = await session.execute(
        select(func.count(func.distinct(ScanEvent.group_id))).where(
            ScanEvent.ca == ca,
            ScanEvent.scanned_at >= since,
        )
    )
    return int(result.scalar_one() or 0)


async def record_scan_event(
    session: AsyncSession,
    *,
    ca: str,
    group_id: int,
    group_name: Optional[str],
    user_id: Optional[int],
    scanned_at: datetime,
    market_cap_usd: Optional[float],
    price_usd: Optional[float],
    scanner_full_name: Optional[str],
    scanner_username: Optional[str],
) -> None:
    group_values: dict = {"group_id": group_id}
    if group_name:
        group_values["name"] = group_name

    group_stmt = insert(Group).values(**group_values)
    if group_name:
        group_stmt = group_stmt.on_conflict_do_update(
            index_elements=[Group.group_id],
            set_={"name": group_name},
        )
    else:
        group_stmt = group_stmt.on_conflict_do_nothing(index_elements=[Group.group_id])

    await session.execute(group_stmt)
    session.add(
        ScanEvent(
            ca=ca,
            group_id=group_id,
            user_id=user_id,
            scanned_at=scanned_at,
            market_cap_usd=market_cap_usd,
            price_usd=price_usd,
            scanner_full_name=scanner_full_name,
            scanner_username=scanner_username,
        )
    )

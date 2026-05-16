from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from sqlalchemy import select, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Group, ScanEvent


@dataclass(frozen=True)
class FirstScanRow:
    user_id: Optional[int]
    scanned_at: datetime


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
        select(ScanEvent.user_id, ScanEvent.scanned_at)
        .where(ScanEvent.ca == ca, ScanEvent.group_id == group_id)
        .order_by(ScanEvent.scanned_at.asc())
        .limit(1)
    )
    row = result.first()
    if row is None:
        return None
    return FirstScanRow(user_id=row[0], scanned_at=row[1])


async def record_scan_event(
    session: AsyncSession,
    *,
    ca: str,
    group_id: int,
    group_name: Optional[str],
    user_id: Optional[int],
    scanned_at: datetime,
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
        )
    )

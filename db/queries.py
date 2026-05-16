from datetime import datetime
from typing import Optional

from sqlalchemy import text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Group, ScanEvent


async def ping_database(session: AsyncSession) -> bool:
    result = await session.execute(text("SELECT 1"))
    return result.scalar_one() == 1


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

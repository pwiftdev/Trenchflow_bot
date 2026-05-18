"""Process-wide resources initialized with the Telegram application."""

from typing import Optional

from config.settings import Settings
from db import runtime as db_runtime
from services.birdeye import BirdeyeClient
from services.dexscreener import DexScreenerClient
from services.helius import HeliusClient

_birdeye: Optional[BirdeyeClient] = None
_dexscreener: Optional[DexScreenerClient] = None
_helius: Optional[HeliusClient] = None


async def startup(settings: Settings) -> None:
    await db_runtime.init_database(settings)

    global _birdeye, _dexscreener, _helius
    if settings.birdeye_api_key:
        _birdeye = BirdeyeClient(
            api_key=settings.birdeye_api_key,
            base_url=settings.birdeye_base_url,
            chain=settings.birdeye_chain,
            timeout_seconds=settings.birdeye_timeout_seconds,
        )
    _dexscreener = DexScreenerClient(
        base_url=settings.dexscreener_base_url,
        timeout_seconds=settings.dexscreener_timeout_seconds,
    )
    if settings.helius_api_key:
        _helius = HeliusClient(
            api_key=settings.helius_api_key,
            timeout_seconds=settings.helius_timeout_seconds,
        )


async def shutdown() -> None:
    global _birdeye, _dexscreener, _helius
    if _birdeye is not None:
        await _birdeye.aclose()
    if _dexscreener is not None:
        await _dexscreener.aclose()
    if _helius is not None:
        await _helius.aclose()
    _birdeye = None
    _dexscreener = None
    _helius = None
    await db_runtime.close_database()


def get_birdeye() -> BirdeyeClient:
    if _birdeye is None:
        from services.birdeye import BirdeyeError

        raise BirdeyeError("BIRDEYE_API_KEY is not configured")
    return _birdeye


def get_dexscreener() -> DexScreenerClient:
    if _dexscreener is None:
        raise RuntimeError("DexScreener client is not initialized")
    return _dexscreener


def get_helius() -> Optional[HeliusClient]:
    return _helius

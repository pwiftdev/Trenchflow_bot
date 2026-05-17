from unittest.mock import AsyncMock, patch

import httpx
import pytest

from services.birdeye import BirdeyeAuthError, BirdeyeClient, TokenNotFoundError


def _client() -> BirdeyeClient:
    return BirdeyeClient(
        api_key="test-key",
        base_url="https://public-api.birdeye.so",
        chain="solana",
        timeout_seconds=5.0,
    )


@pytest.mark.asyncio
async def test_fetch_token_overview_parses_data() -> None:
    response = httpx.Response(
        200,
        json={"success": True, "data": {"symbol": "T", "price": 1.0, "marketCap": 10.0}},
        request=httpx.Request("GET", "https://public-api.birdeye.so/defi/token_overview"),
    )

    with patch("services.birdeye.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.get.return_value = response
        mock_client_cls.return_value = mock_client

        data = await _client().fetch_token_overview(
            "Mint1111111111111111111111111111111111111",
        )

    assert data["symbol"] == "T"
    call_kwargs = mock_client.get.call_args.kwargs
    assert call_kwargs["headers"]["X-API-KEY"] == "test-key"
    assert call_kwargs["headers"]["x-chain"] == "solana"


@pytest.mark.asyncio
async def test_fetch_raises_not_found_when_data_empty() -> None:
    response = httpx.Response(
        200,
        json={"success": True, "data": {}},
        request=httpx.Request("GET", "https://public-api.birdeye.so/defi/token_overview"),
    )

    with patch("services.birdeye.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.get.return_value = response
        mock_client_cls.return_value = mock_client

        with pytest.raises(TokenNotFoundError):
            await _client().fetch_token_overview(
                "Mint1111111111111111111111111111111111111",
            )


@pytest.mark.asyncio
async def test_fetch_raises_on_success_false() -> None:
    response = httpx.Response(
        200,
        json={"success": False, "message": "Token not found"},
        request=httpx.Request("GET", "https://public-api.birdeye.so/defi/token_overview"),
    )

    with patch("services.birdeye.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.get.return_value = response
        mock_client_cls.return_value = mock_client

        with pytest.raises(TokenNotFoundError):
            await _client().fetch_token_overview(
                "Mint1111111111111111111111111111111111111",
            )


@pytest.mark.asyncio
async def test_fetch_raises_birdeye_error_on_401() -> None:
    request = httpx.Request("GET", "https://public-api.birdeye.so/defi/token_overview")
    response = httpx.Response(401, request=request)

    with patch("services.birdeye.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.get.side_effect = httpx.HTTPStatusError(
            "Unauthorized",
            request=request,
            response=response,
        )
        mock_client_cls.return_value = mock_client

        with pytest.raises(BirdeyeAuthError, match="rejected"):
            await _client().fetch_token_overview(
                "Mint1111111111111111111111111111111111111",
            )


@pytest.mark.asyncio
async def test_fetch_holder_profile_uses_token_address_param() -> None:
    response = httpx.Response(
        200,
        json={"success": True, "data": {"holder_summary": {}, "tags": []}},
        request=httpx.Request("GET", "https://public-api.birdeye.so/token/v1/holder-profile"),
    )

    with patch("services.birdeye.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.get.return_value = response
        mock_client_cls.return_value = mock_client

        await _client().fetch_holder_profile("Mint1111111111111111111111111111111111111")

    params = mock_client.get.call_args.kwargs["params"]
    assert params["token_address"] == "Mint1111111111111111111111111111111111111"
    assert params["interval"] == "1h"

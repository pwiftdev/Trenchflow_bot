from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services.helius import HeliusClient


@pytest.mark.asyncio
async def test_fetch_token_image_url_from_json_uri() -> None:
    client = HeliusClient(api_key="test-key", timeout_seconds=5.0)
    asset = {
        "content": {
            "json_uri": "https://example.com/meta.json",
        }
    }

    with patch.object(client, "_rpc_call", AsyncMock(return_value=asset)):
        with patch.object(
            client,
            "_fetch_image_from_metadata_uri",
            AsyncMock(return_value="https://cdn.example.com/icon.png"),
        ) as fetch_json:
            url = await client.fetch_token_image_url("Mint1111111111111111111111111111111111111")

    assert url == "https://cdn.example.com/icon.png"
    fetch_json.assert_awaited_once_with("https://example.com/meta.json")


@pytest.mark.asyncio
async def test_fetch_image_from_metadata_uri_parses_json() -> None:
    client = HeliusClient(api_key="test-key", timeout_seconds=5.0)
    response = MagicMock()
    response.raise_for_status = MagicMock()
    response.json.return_value = {"image": "https://cdn.example.com/from-json.png"}

    mock_http = MagicMock()
    mock_http.get = AsyncMock(return_value=response)
    mock_http.__aenter__ = AsyncMock(return_value=mock_http)
    mock_http.__aexit__ = AsyncMock(return_value=None)

    with patch("services.helius.httpx.AsyncClient", return_value=mock_http):
        url = await client._fetch_image_from_metadata_uri("https://example.com/meta.json")

    assert url == "https://cdn.example.com/from-json.png"

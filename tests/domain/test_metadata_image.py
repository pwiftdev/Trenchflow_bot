from domain.metadata_image import (
    image_url_from_helius_asset,
    image_url_from_metadata_json,
    resolve_content_uri,
)


def test_resolve_content_uri_ipfs() -> None:
    assert (
        resolve_content_uri("ipfs://bafybeigdyrzt5sfp7udm7q")
        == "https://ipfs.io/ipfs/bafybeigdyrzt5sfp7udm7q"
    )


def test_image_url_from_metadata_json() -> None:
    url = image_url_from_metadata_json(
        {
            "name": "Test",
            "image": "ipfs://QmImageHash",
        }
    )
    assert url == "https://ipfs.io/ipfs/QmImageHash"


def test_image_url_from_helius_asset_links() -> None:
    asset = {
        "content": {
            "links": {"image": "https://cdn.example.com/token.png"},
            "json_uri": "https://example.com/meta.json",
        }
    }
    assert image_url_from_helius_asset(asset) == "https://cdn.example.com/token.png"


def test_image_url_from_helius_asset_files_fallback() -> None:
    asset = {
        "content": {
            "files": [{"uri": "https://cdn.example.com/from-file.jpg"}],
            "json_uri": "https://example.com/meta.json",
        }
    }
    assert image_url_from_helius_asset(asset) == "https://cdn.example.com/from-file.jpg"

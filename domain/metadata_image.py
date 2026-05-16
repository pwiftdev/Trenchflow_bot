from typing import Any, Optional


def resolve_content_uri(uri: str) -> Optional[str]:
    cleaned = uri.strip()
    if not cleaned:
        return None
    if cleaned.startswith("https://"):
        return cleaned
    if cleaned.startswith("http://"):
        return cleaned
    if cleaned.startswith("ipfs://"):
        path = cleaned[7:]
        if path.startswith("ipfs/"):
            path = path[5:]
        return f"https://ipfs.io/ipfs/{path}"
    if cleaned.startswith("ar://"):
        return f"https://arweave.net/{cleaned[5:]}"
    return None


def image_url_from_helius_asset(asset: Any) -> Optional[str]:
    if not isinstance(asset, dict):
        return None

    content = asset.get("content")
    if not isinstance(content, dict):
        return None

    links = content.get("links")
    if isinstance(links, dict):
        for key in ("image", "animation_url"):
            url = _normalize_image_url(links.get(key))
            if url:
                return url

    files = content.get("files")
    if isinstance(files, list):
        for entry in files:
            if not isinstance(entry, dict):
                continue
            url = _normalize_image_url(entry.get("uri") or entry.get("cdn_uri"))
            if url:
                return url

    return None


def metadata_json_uri_from_asset(asset: Any) -> Optional[str]:
    if not isinstance(asset, dict):
        return None
    content = asset.get("content")
    if not isinstance(content, dict):
        return None
    json_uri = content.get("json_uri")
    if isinstance(json_uri, str) and json_uri.strip():
        return json_uri.strip()
    return None


def image_url_from_metadata_json(payload: Any) -> Optional[str]:
    if not isinstance(payload, dict):
        return None

    image = payload.get("image")
    if isinstance(image, str):
        url = _normalize_image_url(image)
        if url:
            return url

    if isinstance(image, dict):
        url = _normalize_image_url(image.get("uri") or image.get("url"))
        if url:
            return url

    properties = payload.get("properties")
    if isinstance(properties, dict):
        files = properties.get("files")
        if isinstance(files, list):
            for entry in files:
                if not isinstance(entry, dict):
                    continue
                url = _normalize_image_url(entry.get("uri") or entry.get("url"))
                if url:
                    return url

    return None


def _normalize_image_url(value: Any) -> Optional[str]:
    if not isinstance(value, str):
        return None
    if value.startswith("data:"):
        return None
    resolved = resolve_content_uri(value)
    if resolved is None:
        return None
    if not resolved.startswith("http"):
        return None
    return resolved

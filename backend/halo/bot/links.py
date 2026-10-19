"""Signed deep links that connect a brand to the Telegram chat where Halo posts new matches."""

import hashlib
import hmac

from halo.config import get_settings


def _signature(brand_id: int) -> str:
    key = get_settings().secret_key.encode()
    return hmac.new(key, f"brand:{brand_id}".encode(), hashlib.sha256).hexdigest()[:16]


def brand_start_payload(brand_id: int) -> str:
    return f"brand-{brand_id}-{_signature(brand_id)}"


def brand_link(brand_id: int) -> str:
    return f"https://t.me/{get_settings().telegram_bot_username}?start={brand_start_payload(brand_id)}"


def parse_brand_payload(payload: str) -> int | None:
    parts = payload.split("-")
    if len(parts) != 3 or parts[0] != "brand" or not parts[1].isdigit():
        return None
    brand_id = int(parts[1])
    return brand_id if hmac.compare_digest(parts[2], _signature(brand_id)) else None

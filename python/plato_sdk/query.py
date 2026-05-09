"""Room query utilities (prefix filter, search)."""

from __future__ import annotations

from typing import Any, Callable, Dict, List


def filter_rooms(
    rooms: Dict[str, Any],
    prefix: str | None = None,
    min_tiles: int | None = None,
    predicate: Callable[[str, Dict[str, Any]], bool] | None = None,
) -> Dict[str, Any]:
    """Filter a rooms dict by various criteria.

    Args:
        rooms: Dict from :meth:`PlatoClient.rooms`.
        prefix: Room ID prefix filter.
        min_tiles: Minimum tile count.
        predicate: Arbitrary filter function ``(room_id, room_data) → bool``.

    Returns:
        Filtered dict.
    """
    result = dict(rooms)
    if prefix:
        result = {k: v for k, v in result.items() if k.startswith(prefix)}
    if min_tiles is not None:
        result = {k: v for k, v in result.items() if v.get("tile_count", 0) >= min_tiles}
    if predicate:
        result = {k: v for k, v in result.items() if predicate(k, v)}
    return result


def group_by_prefix(rooms: Dict[str, Any], separator: str = "_") -> Dict[str, List[str]]:
    """Group room IDs by their prefix (up to separator).

    Args:
        rooms: Dict from :meth:`PlatoClient.rooms`.
        separator: Prefix separator character.

    Returns:
        Dict mapping prefix → list of room IDs.
    """
    groups: Dict[str, List[str]] = {}
    for room_id in sorted(rooms):
        parts = room_id.split(separator, 1)
        prefix = parts[0] if len(parts) > 1 else room_id
        groups.setdefault(prefix, []).append(room_id)
    return groups

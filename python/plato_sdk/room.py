"""Room management helpers."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class Room:
    """Represents a PLATO room.

    Attributes:
        id: Room identifier.
        tile_count: Number of tiles in the room.
        created: Creation timestamp.
        tiles: List of tile dicts (populated after fetching details).
    """

    id: str
    tile_count: int = 0
    created: Optional[str] = None
    tiles: List[Dict[str, Any]] = field(default_factory=list)

    @classmethod
    def from_dict(cls, room_id: str, data: Dict[str, Any]) -> "Room":
        return cls(
            id=room_id,
            tile_count=data.get("tile_count", 0),
            created=data.get("created"),
        )

    @classmethod
    def from_detail(cls, room_id: str, data: Dict[str, Any]) -> "Room":
        tiles = data.get("tiles", [])
        return cls(
            id=room_id,
            tile_count=len(tiles),
            created=data.get("created"),
            tiles=tiles,
        )

    @property
    def stats(self) -> Dict[str, Any]:
        """Quick stats dict."""
        return {
            "room_id": self.id,
            "tile_count": self.tile_count,
            "created": self.created,
        }

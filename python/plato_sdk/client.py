"""PLATO HTTP client."""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError


class PlatoClient:
    """Client for the PLATO tile-based knowledge store.

    Args:
        base_url: PLATO server URL (e.g. ``"http://147.224.38.131:8847"``).
        timeout: Request timeout in seconds.
    """

    def __init__(self, base_url: str, timeout: int = 30) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get(self, path: str) -> Any:
        url = f"{self.base_url}{path}"
        req = Request(url, method="GET")
        req.add_header("Accept", "application/json")
        with urlopen(req, timeout=self.timeout) as resp:
            return json.loads(resp.read())

    def _post(self, path: str, body: dict) -> Any:
        data = json.dumps(body).encode()
        url = f"{self.base_url}{path}"
        req = Request(url, data=data, method="POST")
        req.add_header("Content-Type", "application/json")
        req.add_header("Accept", "application/json")
        with urlopen(req, timeout=self.timeout) as resp:
            return json.loads(resp.read())

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def rooms(self, prefix: Optional[str] = None) -> Dict[str, Any]:
        """List all rooms.

        Args:
            prefix: Optional prefix filter (client-side).

        Returns:
            Dict mapping room_id → room metadata (tile_count, created).
        """
        data = self._get("/rooms")
        if prefix:
            data = {k: v for k, v in data.items() if k.startswith(prefix)}
        return data

    def room(self, room_id: str) -> Dict[str, Any]:
        """Get room details including all tiles.

        Args:
            room_id: The room identifier.

        Returns:
            Dict with ``tiles`` list and room metadata.
        """
        return self._get(f"/room/{room_id}")

    def submit(self, room_id: str, tile: dict) -> Any:
        """Submit a tile to a room.

        Args:
            room_id: Target room.
            tile: Tile dict (use :class:`TileBuilder` to construct).

        Returns:
            Server response (usually the created tile with provenance).
        """
        return self._post(f"/room/{room_id}/tile", tile)

    def search(self, query: str) -> List[Dict[str, Any]]:
        """Client-side full-text search across all rooms.

        Searches tile ``question`` and ``answer`` fields for the query string.

        Args:
            query: Search term (case-insensitive).

        Returns:
            List of matching tiles with an added ``_room`` field.
        """
        results: List[Dict[str, Any]] = []
        q = query.lower()
        all_rooms = self._get("/rooms")
        for room_id in all_rooms:
            room_data = self._get(f"/room/{room_id}")
            for tile in room_data.get("tiles", []):
                searchable = (
                    tile.get("question", "") + " " + tile.get("answer", "")
                ).lower()
                if q in searchable:
                    tile_copy = dict(tile)
                    tile_copy["_room"] = room_id
                    results.append(tile_copy)
        return results

    def rooms_with_tag(self, tag: str) -> List[str]:
        """Find rooms that contain tiles with a specific tag.

        Args:
            tag: Tag string to search for.

        Returns:
            List of room IDs containing tiles with that tag.
        """
        matched: List[str] = []
        all_rooms = self._get("/rooms")
        for room_id in all_rooms:
            room_data = self._get(f"/room/{room_id}")
            for tile in room_data.get("tiles", []):
                if tag in tile.get("tags", []):
                    matched.append(room_id)
                    break
        return matched

    # ------------------------------------------------------------------
    # Convenience
    # ------------------------------------------------------------------

    def ping(self) -> bool:
        """Check if the PLATO server is reachable."""
        try:
            self._get("/rooms")
            return True
        except (URLError, HTTPError, OSError):
            return False

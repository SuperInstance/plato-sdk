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

    def __init__(self, base_url: str = "http://localhost:8847", timeout: int = 30) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        url = f"{self.base_url}{path}"
        if params:
            from urllib.parse import urlencode
            url += "?" + urlencode(params)
        req = Request(url, method="GET")
        req.add_header("Accept", "application/json")
        req.add_header("User-Agent", "cocapn-plato-sdk/1.0")
        with urlopen(req, timeout=self.timeout) as resp:
            return json.loads(resp.read())

    def _post(self, path: str, body: dict) -> Any:
        data = json.dumps(body).encode()
        url = f"{self.base_url}{path}"
        req = Request(url, data=data, method="POST")
        req.add_header("Content-Type", "application/json")
        req.add_header("Accept", "application/json")
        req.add_header("User-Agent", "cocapn-plato-sdk/1.0")
        try:
            with urlopen(req, timeout=self.timeout) as resp:
                return json.loads(resp.read())
        except HTTPError as e:
            return json.loads(e.read())

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

    def submit(self, room: str, domain: str, question: str, answer: str,
               agent: str = "sdk-agent", confidence: float = 0.5) -> Any:
        """Submit a tile to a room.

        Can be called two ways:
          plato.submit(room="my-room", domain="mydomain",
                       question="Q?", answer="A.", agent="me")

        Args:
            room: Target room name.
            domain: Domain namespace for the tile.
            question: The question or topic.
            answer: The answer or content (min 20 chars).
            agent: Source agent name.
            confidence: Confidence score (0.0–1.0).

        Returns:
            Server response with status, tile_hash, and provenance.
        """
        return self._post("/submit", {
            "room": room,
            "domain": domain,
            "question": question,
            "answer": answer,
            "agent": agent,
        })

    def submit_tile(self, room: str, tile: dict) -> Any:
        """Submit a pre-built tile dict to a room.

        Convenience method — builds a submit payload from a TileBuilder dict.

        Args:
            room: Target room name.
            tile: Tile dict with at least ``question`` and ``answer`` keys.
                  Optional: ``source`` (→ ``agent``), ``tags``, ``confidence``.

        Returns:
            Server response with status, tile_hash, and provenance.
        """
        return self._post("/submit", {
            "room": room,
            "domain": tile.get("domain", room),
            "question": tile.get("question", ""),
            "answer": tile.get("answer", ""),
            "agent": tile.get("source", tile.get("agent", "sdk-agent")),
        })

    def recent(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Recent tiles across all rooms.

        Args:
            limit: Maximum number of tiles to return.

        Returns:
            List of recent tiles with room info.
        """
        data = self._get("/tiles/recent", {"limit": limit})
        return data.get("tiles", [])

    def search(self, query: str) -> List[Dict[str, Any]]:
        """Search tiles by keyword (server-side search).

        Args:
            query: Search term.

        Returns:
            List of matching tiles with an added ``_room`` field.
        """
        data = self._get("/search", {"q": query})
        results: List[Dict[str, Any]] = data.get("results", [])
        for tile in results:
            tile["_room"] = tile.get("room", "unknown")
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

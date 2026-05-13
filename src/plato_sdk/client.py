"""
PlatoClient — Connect to any PLATO server.

Usage:
    client = PlatoClient("http://localhost:8847")
    rooms = client.rooms()
    client.submit(room="my-room", question="Q?", answer="A...", agent="me")
"""

import json
from typing import Optional
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from urllib.parse import urlencode


class PlatoClient:
    """HTTP client for a PLATO server."""

    def __init__(self, url: str = "http://localhost:8847", timeout: int = 30):
        self.url = url.rstrip("/")
        self.timeout = timeout

    def _get(self, path: str, params: dict = None) -> dict:
        url = f"{self.url}{path}"
        if params:
            url += "?" + urlencode(params)
        req = Request(url)
        req.add_header("User-Agent", "cocapn-plato-sdk/1.0")
        resp = urlopen(req, timeout=self.timeout)
        return json.loads(resp.read())

    def _post(self, path: str, body: dict) -> dict:
        data = json.dumps(body).encode()
        req = Request(f"{self.url}{path}", data=data, method="POST")
        req.add_header("Content-Type", "application/json")
        req.add_header("User-Agent", "cocapn-plato-sdk/1.0")
        try:
            resp = urlopen(req, timeout=self.timeout)
            return json.loads(resp.read())
        except HTTPError as e:
            return json.loads(e.read())

    # ── Knowledge ──────────────────────────────────────────
    def status(self) -> dict:
        """Server status."""
        return self._get("/")

    def rooms(self) -> dict:
        """All rooms with tile counts."""
        return self._get("/rooms")

    def room(self, name: str) -> dict:
        """Get tiles in a room."""
        return self._get(f"/room/{name}")

    def recent(self, limit: int = 50) -> list:
        """Recent tiles across all rooms."""
        return self._get("/tiles/recent", {"limit": limit}).get("tiles", [])

    def search(self, query: str) -> list:
        """Search tiles by keyword."""
        return self._get("/search", {"q": query}).get("results", [])

    def submit(self, room: str, domain: str, question: str, answer: str,
               agent: str = "sdk-agent", confidence: float = 0.5,
               t_minus_event: str = None) -> dict:
        """Submit a knowledge tile.

        Returns dict with at least 'status', 'tile_hash', and 'lamport' (v3).
        If t_minus_event is set, the tile is filed as simulation-first.
        """
        body = {
            "room": room,
            "domain": domain,
            "question": question,
            "answer": answer,
            "agent": agent,
            "confidence": confidence,
        }
        if t_minus_event is not None:
            body["t_minus_event"] = t_minus_event
        return self._post("/submit", body)

    def submit_tile(self, room: str, tile_dict: dict) -> dict:
        """Submit a pre-built tile dict (e.g. from TileBuilder)."""
        body = dict(tile_dict)
        body["room"] = room
        if "domain" not in body:
            body["domain"] = "general"
        return self._post("/submit", body)

    def stats(self) -> dict:
        """Aggregate server statistics (v3)."""
        return self._get("/stats")

    def retract_tile(self, room: str, tile_hash: str, reason: str = "") -> dict:
        """Retract a tile by hash (v3 lifecycle)."""
        return self._post("/retract", {
            "room": room,
            "tile_hash": tile_hash,
            "reason": reason,
        })

    def supersede_tile(self, room: str, old_hash: str, new_tile: dict) -> dict:
        """Replace a tile with a new one (v3 lifecycle).

        new_tile should contain at least 'question' and 'answer'.
        Returns dict with 'status', 'old_hash', 'new_hash', 'lamport'.
        """
        body = {
            "room": room,
            "old_hash": old_hash,
            "new_tile": new_tile,
        }
        return self._post("/supersede", body)

    def get_active_tiles(self, room: str) -> list:
        """Get only Active-state tiles from a room (v3).

        Filters server-side or client-side to tiles whose 'state' field
        is 'Active' or absent (legacy tiles treated as active).
        """
        data = self.room(room)
        tiles = data.get("tiles", [])
        return [t for t in tiles if t.get("state", "Active") == "Active"]

    # ── Agent Spawner ──────────────────────────────────────
    def armor_catalog(self) -> dict:
        """Available armor types."""
        return self._get("/armor")

    def keys(self) -> dict:
        """Configured API providers."""
        return self._get("/keys")

    def spawn(self, description: str, room: str = "general",
              provider: str = None, model: str = None,
              temperature: float = 0.7) -> dict:
        """Spawn an agent. Returns session info + first response."""
        body = {
            "description": description,
            "room": room,
            "temperature": temperature,
        }
        if provider:
            body["provider"] = provider
        if model:
            body["model"] = model
        return self._post("/spawn", body)

    def chat(self, session_id: str, message: str,
             temperature: float = 0.7) -> dict:
        """Send a message to a spawned agent session."""
        return self._post(f"/agent/{session_id}/chat", {
            "message": message,
            "temperature": temperature,
        })

    def agent_submit(self, session_id: str, room: str, domain: str,
                     question: str, answer: str) -> dict:
        """Submit a tile on behalf of an agent session."""
        return self._post(f"/agent/{session_id}/submit", {
            "room": room,
            "domain": domain,
            "question": question,
            "answer": answer,
        })

    # ── Fleet Sync ─────────────────────────────────────────
    def sync_status(self) -> dict:
        """Fleet sync status."""
        return self._get("/sync/status")

    def sync_toggle(self, enabled: bool = True) -> dict:
        """Enable/disable fleet sync."""
        return self._post("/sync/toggle", {"enabled": enabled})

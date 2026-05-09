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
               agent: str = "sdk-agent", confidence: float = 0.5) -> dict:
        """Submit a knowledge tile."""
        return self._post("/submit", {
            "room": room,
            "domain": domain,
            "question": question,
            "answer": answer,
            "agent": agent,
        })

    def stats(self) -> dict:
        """Usage statistics."""
        return self._get("/stats")

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

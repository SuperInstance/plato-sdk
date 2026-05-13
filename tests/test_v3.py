"""Tests for PLATO SDK v3 features."""

import json
import unittest
from unittest.mock import patch, MagicMock
from io import BytesIO
from urllib.error import HTTPError

from plato_sdk import PlatoClient, TileBuilder


def _mock_response(data, status=200):
    """Create a mock HTTP response with JSON body."""
    resp = MagicMock()
    resp.read.return_value = json.dumps(data).encode()
    return resp


def _mock_http_error(data, status=400):
    """Create a mock HTTPError."""
    err = HTTPError("http://test", status, "Bad", {}, BytesIO(json.dumps(data).encode()))
    return err


class TestPlatoClient(unittest.TestCase):
    def setUp(self):
        self.client = PlatoClient("http://localhost:8847")

    # ── Existing methods (regression) ────────────────────
    @patch("plato_sdk.client.urlopen")
    def test_ping(self, mock_urlopen):
        mock_urlopen.return_value = _mock_response({"status": "ok"})
        result = self.client.status()
        self.assertEqual(result["status"], "ok")

    @patch("plato_sdk.client.urlopen")
    def test_rooms(self, mock_urlopen):
        mock_urlopen.return_value = _mock_response({"room1": {"tile_count": 5}})
        result = self.client.rooms()
        self.assertIn("room1", result)

    @patch("plato_sdk.client.urlopen")
    def test_room(self, mock_urlopen):
        mock_urlopen.return_value = _mock_response({
            "room_id": "test", "tile_count": 2,
            "tiles": [{"question": "Q1", "answer": "A1"}],
        })
        result = self.client.room("test")
        self.assertEqual(result["room_id"], "test")
        self.assertEqual(len(result["tiles"]), 1)

    @patch("plato_sdk.client.urlopen")
    def test_submit(self, mock_urlopen):
        mock_urlopen.return_value = _mock_response({
            "status": "accepted", "tile_hash": "abc123", "lamport": 42,
        })
        result = self.client.submit(
            room="test", domain="sdk", question="Q?", answer="A" * 20,
        )
        self.assertEqual(result["status"], "accepted")
        self.assertEqual(result["tile_hash"], "abc123")

    # ── v3: submit with lamport ──────────────────────────
    @patch("plato_sdk.client.urlopen")
    def test_submit_returns_lamport(self, mock_urlopen):
        mock_urlopen.return_value = _mock_response({
            "status": "accepted", "tile_hash": "h1", "lamport": 7,
        })
        result = self.client.submit(
            room="test", domain="sdk", question="Q?", answer="A" * 20,
        )
        self.assertIn("lamport", result)
        self.assertEqual(result["lamport"], 7)

    # ── v3: submit with t_minus_event ────────────────────
    @patch("plato_sdk.client.urlopen")
    def test_submit_with_t_minus_event(self, mock_urlopen):
        mock_urlopen.return_value = _mock_response({
            "status": "accepted", "tile_hash": "h2", "lamport": 8,
        })
        result = self.client.submit(
            room="test", domain="sdk", question="Q?", answer="A" * 20,
            t_minus_event="T-3h: calibration cycle",
        )
        self.assertEqual(result["status"], "accepted")
        # Verify the body included t_minus_event
        call_args = mock_urlopen.call_args
        req = call_args[0][0]
        body = json.loads(req.data)
        self.assertEqual(body["t_minus_event"], "T-3h: calibration cycle")

    @patch("plato_sdk.client.urlopen")
    def test_submit_without_t_minus_event(self, mock_urlopen):
        mock_urlopen.return_value = _mock_response({
            "status": "accepted", "tile_hash": "h3", "lamport": 9,
        })
        self.client.submit(
            room="test", domain="sdk", question="Q?", answer="A" * 20,
        )
        call_args = mock_urlopen.call_args
        req = call_args[0][0]
        body = json.loads(req.data)
        self.assertNotIn("t_minus_event", body)

    # ── v3: get_stats ────────────────────────────────────
    @patch("plato_sdk.client.urlopen")
    def test_get_stats(self, mock_urlopen):
        mock_urlopen.return_value = _mock_response({
            "rooms": 42, "tiles": 1337, "agents": 5,
        })
        result = self.client.stats()
        self.assertEqual(result["rooms"], 42)
        self.assertEqual(result["tiles"], 1337)

    # ── v3: retract_tile ────────────────────────────────
    @patch("plato_sdk.client.urlopen")
    def test_retract_tile(self, mock_urlopen):
        mock_urlopen.return_value = _mock_response({
            "status": "retracted", "tile_hash": "abc123",
        })
        result = self.client.retract_tile("test-room", "abc123", "outdated")
        self.assertEqual(result["status"], "retracted")
        call_args = mock_urlopen.call_args
        req = call_args[0][0]
        body = json.loads(req.data)
        self.assertEqual(body["room"], "test-room")
        self.assertEqual(body["tile_hash"], "abc123")
        self.assertEqual(body["reason"], "outdated")

    @patch("plato_sdk.client.urlopen")
    def test_retract_tile_no_reason(self, mock_urlopen):
        mock_urlopen.return_value = _mock_response({
            "status": "retracted", "tile_hash": "abc123",
        })
        self.client.retract_tile("room", "abc123")
        body = json.loads(mock_urlopen.call_args[0][0].data)
        self.assertEqual(body["reason"], "")

    # ── v3: supersede_tile ───────────────────────────────
    @patch("plato_sdk.client.urlopen")
    def test_supersede_tile(self, mock_urlopen):
        mock_urlopen.return_value = _mock_response({
            "status": "superseded",
            "old_hash": "old123",
            "new_hash": "new456",
            "lamport": 15,
        })
        new_tile = {"question": "Updated Q?", "answer": "Updated A" * 5}
        result = self.client.supersede_tile("test-room", "old123", new_tile)
        self.assertEqual(result["status"], "superseded")
        self.assertEqual(result["old_hash"], "old123")
        self.assertEqual(result["new_hash"], "new456")
        self.assertIn("lamport", result)

        body = json.loads(mock_urlopen.call_args[0][0].data)
        self.assertEqual(body["room"], "test-room")
        self.assertEqual(body["old_hash"], "old123")
        self.assertEqual(body["new_tile"], new_tile)

    # ── v3: get_active_tiles ────────────────────────────
    @patch("plato_sdk.client.urlopen")
    def test_get_active_tiles(self, mock_urlopen):
        mock_urlopen.return_value = _mock_response({
            "room_id": "test", "tile_count": 4,
            "tiles": [
                {"question": "Q1", "answer": "A1", "state": "Active"},
                {"question": "Q2", "answer": "A2", "state": "Retracted"},
                {"question": "Q3", "answer": "A3"},  # legacy, no state
                {"question": "Q4", "answer": "A4", "state": "Superseded"},
            ],
        })
        result = self.client.get_active_tiles("test")
        self.assertEqual(len(result), 2)
        questions = [t["question"] for t in result]
        self.assertIn("Q1", questions)
        self.assertIn("Q3", questions)
        self.assertNotIn("Q2", questions)
        self.assertNotIn("Q4", questions)

    @patch("plato_sdk.client.urlopen")
    def test_get_active_tiles_empty(self, mock_urlopen):
        mock_urlopen.return_value = _mock_response({
            "room_id": "empty", "tile_count": 0, "tiles": [],
        })
        result = self.client.get_active_tiles("empty")
        self.assertEqual(result, [])

    # ── v3: submit_tile (TileBuilder dict) ──────────────
    @patch("plato_sdk.client.urlopen")
    def test_submit_tile(self, mock_urlopen):
        mock_urlopen.return_value = _mock_response({
            "status": "accepted", "tile_hash": "tb1", "lamport": 10,
        })
        tile = TileBuilder().question("Q?").answer("A" * 20).source("test").build()
        result = self.client.submit_tile("my-room", tile)
        self.assertEqual(result["status"], "accepted")
        body = json.loads(mock_urlopen.call_args[0][0].data)
        self.assertEqual(body["room"], "my-room")
        self.assertEqual(body["question"], "Q?")


class TestTileBuilder(unittest.TestCase):
    def test_basic_build(self):
        tile = (
            TileBuilder()
            .question("What is drift?")
            .answer("Deviation from expected constraint values.")
            .source("forgemaster")
            .tag("constraint", "drift")
            .confidence(0.95)
            .build()
        )
        self.assertEqual(tile["question"], "What is drift?")
        self.assertIn("constraint", tile["tags"])
        self.assertAlmostEqual(tile["confidence"], 0.95)

    def test_t_minus_event(self):
        tile = (
            TileBuilder()
            .question("Q?")
            .answer("A" * 20)
            .t_minus_event("T-3h: calibration cycle")
            .build()
        )
        self.assertEqual(tile["t_minus_event"], "T-3h: calibration cycle")

    def test_no_t_minus_event_when_unset(self):
        tile = TileBuilder().question("Q?").answer("A" * 20).build()
        self.assertNotIn("t_minus_event", tile)

    def test_confidence_clamped(self):
        tile = TileBuilder().confidence(1.5).build()
        self.assertLessEqual(tile["confidence"], 1.0)
        tile = TileBuilder().confidence(-0.5).build()
        self.assertGreaterEqual(tile["confidence"], 0.0)

    def test_fluent_api(self):
        """All methods return self for chaining."""
        builder = TileBuilder()
        for method in ["question", "answer", "content", "source", "provenance",
                        "domain", "t_minus_event"]:
            result = getattr(builder, method)("x")
            self.assertIs(result, builder)
        self.assertIs(builder.tag("a"), builder)
        self.assertIs(builder.tags(["b"]), builder)
        self.assertIs(builder.confidence(0.5), builder)


if __name__ == "__main__":
    unittest.main()

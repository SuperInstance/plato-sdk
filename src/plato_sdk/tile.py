"""Tile builder for constructing PLATO tiles."""

from __future__ import annotations

from typing import Any, Dict, List, Optional


class TileBuilder:
    """Fluent builder for PLATO tiles.

    Usage::

        tile = (TileBuilder()
            .question("What is drift?")
            .answer("Drift is the deviation from expected constraint values")
            .source("forgemaster")
            .tag("constraint", "drift")
            .confidence(0.95)
            .t_minus_event("T-3h: calibration cycle")
            .build())
    """

    def __init__(self) -> None:
        self._question: Optional[str] = None
        self._answer: Optional[str] = None
        self._source: Optional[str] = None
        self._tags: List[str] = []
        self._confidence: float = 0.0
        self._domain: Optional[str] = None
        self._t_minus_event: Optional[str] = None

    def question(self, text: str) -> "TileBuilder":
        self._question = text
        return self

    def answer(self, text: str) -> "TileBuilder":
        self._answer = text
        return self

    def content(self, text: str) -> "TileBuilder":
        """Alias for ``answer()``."""
        self._answer = text
        return self

    def source(self, source: str) -> "TileBuilder":
        self._source = source
        return self

    def provenance(self, source: str) -> "TileBuilder":
        """Alias for ``source()``."""
        self._source = source
        return self

    def tag(self, *tags: str) -> "TileBuilder":
        self._tags.extend(tags)
        return self

    def tags(self, tags: List[str]) -> "TileBuilder":
        self._tags.extend(tags)
        return self

    def confidence(self, value: float) -> "TileBuilder":
        self._confidence = max(0.0, min(1.0, value))
        return self

    def domain(self, domain: str) -> "TileBuilder":
        self._domain = domain
        return self

    def t_minus_event(self, value: str) -> "TileBuilder":
        """Set the simulation-first countdown event (v3).

        Describes when this tile's knowledge becomes actionable relative
        to a planned event, e.g. ``"T-3h: calibration cycle"``.
        """
        self._t_minus_event = value
        return self

    def build(self) -> Dict[str, Any]:
        """Build the tile dict."""
        tile: Dict[str, Any] = {
            "question": self._question or "",
            "answer": self._answer or "",
            "tags": list(self._tags),
            "confidence": self._confidence,
        }
        if self._source:
            tile["source"] = self._source
        if self._domain:
            tile["domain"] = self._domain
        if self._t_minus_event is not None:
            tile["t_minus_event"] = self._t_minus_event
        return tile

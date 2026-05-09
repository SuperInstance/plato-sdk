#!/usr/bin/env python3
"""Fleet bridge — sync tiles between PLATO rooms."""

from plato_sdk import PlatoClient, TileBuilder

PLATO_URL = "http://147.224.38.131:8847"


def bridge_room(source_room: str, target_room: str, tag_filter: str | None = None):
    """Copy tiles from source room to target room, optionally filtering by tag."""
    plato = PlatoClient(PLATO_URL)
    source = plato.room(source_room)
    copied = 0

    for tile in source.get("tiles", []):
        if tag_filter and tag_filter not in tile.get("tags", []):
            continue
        # Build a new tile from the source
        new_tile = (
            TileBuilder()
            .question(tile.get("question", ""))
            .answer(tile.get("answer", ""))
            .source(f"bridge:{tile.get('source', 'unknown')}")
            .tags(tile.get("tags", []))
            .confidence(tile.get("confidence", 0.0))
            .domain(target_room)
            .build()
        )
        plato.submit(target_room, new_tile)
        copied += 1

    return copied


if __name__ == "__main__":
    n = bridge_room("fleet_health", "forge", tag_filter="status")
    print(f"Bridged {n} tiles")

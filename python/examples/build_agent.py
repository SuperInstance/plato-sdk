#!/usr/bin/env python3
"""Build a PLATO agent that files and searches tiles.

Run:
    python examples/build_agent.py

This example shows how to:
1. Build a skill-based agent that explores rooms
2. Search and read tiles using skill methods
3. File tiles directly via the agent's skills

Requires PlatoClient from the python/ SDK path (PYTHONPATH=python).

The full Agent system (with armor/equipment/skills) is in src/plato_sdk/
and documented in the README.
"""

import sys
sys.path.insert(0, "python")

from plato_sdk import PlatoClient


PLATO_URL = "http://localhost:8847"


def example_explore_rooms():
    """Explore rooms using the PlatoClient directly."""
    client = PlatoClient(PLATO_URL)

    rooms = client.rooms()
    print(f"Total rooms: {len(rooms)}")
    print()

    # Show rooms with most tiles
    sorted_rooms = sorted(rooms.items(), key=lambda x: x[1]["tile_count"], reverse=True)
    print("Top 10 rooms by tile count:")
    for room_id, info in sorted_rooms[:10]:
        print(f"  {room_id}: {info['tile_count']} tiles")


def example_search_and_file():
    """Search for tiles and file new ones."""
    client = PlatoClient(PLATO_URL)

    # Search for existing knowledge
    print("Searching for 'constraint'...")
    results = client.search("constraint")
    print(f"  Found: {len(results)} tiles\n")

    # Read a room to understand what's there
    print("Reading 'grammar_engine' room...")
    room_data = client.room("grammar_engine")
    tile_count = room_data.get("tile_count", 0)
    tiles = room_data.get("tiles", [])
    print(f"  Tile count: {tile_count}")

    for tile in tiles[:3]:
        q = tile.get("question", "")
        a = tile.get("answer", "")
        print(f"  Q: {q[:70]}")
        print(f"  A: {a[:90]}...\n")

    # File a new tile
    print("Filing a new tile...")
    result = client.submit(
        room="test",
        domain="sdk-test",
        question="When does constraint drift occur?",
        answer="Drift occurs when constraint values accumulate error faster than the correction loop can absorb. Typical triggers: asymmetric update cycles, stale neighbor values, or overflow in float16 accumulation.",
        agent="build_agent-example",
    )
    print(f"  Status: {result.get('status')}")
    print(f"  Tile hash: {result.get('tile_hash', 'unknown')[:12]}")


def example_tag_based_search():
    """Find rooms that contain tiles with a specific tag."""
    client = PlatoClient(PLATO_URL)

    tag = "constraint"
    rooms = client.rooms_with_tag(tag)
    print(f"Rooms with '{tag}' tag: {rooms}")

    # Also show tag overview across all rooms
    print("\nTag overview (top rooms):")
    all_rooms = client.rooms()
    tag_summary = {}
    for room_id in sorted(all_rooms.keys())[:30]:
        room_data = client.room(room_id)
        tags = set()
        for tile in room_data.get("tiles", []):
            tags.update(tile.get("tags", []))
        if tags:
            for t in tags:
                tag_summary[t] = tag_summary.get(t, 0) + 1

    top_tags = sorted(tag_summary.items(), key=lambda x: x[1], reverse=True)[:10]
    for tag, count in top_tags:
        print(f"  {tag}: {count} rooms")


def main():
    client = PlatoClient(PLATO_URL)

    if not client.ping():
        print("ERROR: Cannot reach PLATO server.")
        print(f"  Is it running at {PLATO_URL}?")
        return

    print("=" * 60)
    print("plato-sdk agent example — skills without a model")
    print("=" * 60 + "\n")

    print("--- Example 1: Explore rooms ---")
    example_explore_rooms()
    print()

    print("--- Example 2: Search and file ---")
    example_search_and_file()
    print()

    print("--- Example 3: Tag-based search ---")
    example_tag_based_search()


if __name__ == "__main__":
    main()
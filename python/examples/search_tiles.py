#!/usr/bin/env python3
"""Search PLATO tiles by keyword.

Run:
    python examples/search_tiles.py

Search is case-insensitive and matches against both question and answer fields.
It's a client-side full-text scan — no server-side index required.
"""

from plato_sdk import PlatoClient

PLATO_URL = "http://localhost:8847"


def search_by_tag(plato: PlatoClient, tag: str):
    """Find rooms that contain tiles with a specific tag."""
    rooms = plato.rooms_with_tag(tag)
    return rooms


def main():
    plato = PlatoClient(PLATO_URL)

    if not plato.ping():
        print("ERROR: Cannot reach PLATO server.")
        return

    # ── Example 1: Basic keyword search ──────────────────────────
    query = "drift"

    print(f"Searching for: '{query}'")
    print("-" * 50)

    results = plato.search(query)
    print(f"{len(results)} matches found\n")

    for tile in results:
        room = tile.get("_room", "?")
        question = tile.get("question", "")
        answer = tile.get("answer", "")
        source = tile.get("source", "unknown")
        confidence = tile.get("confidence", 0.0)

        print(f"[{room}] {question}")
        print(f"  {answer[:150]}{'...' if len(answer) > 150 else ''}")
        print(f"  source: {source}, confidence: {confidence:.2f}")
        print()

    # ── Example 2: Search by tag ─────────────────────────────────
    tag = "constraint"

    print(f"\nRooms with tag '{tag}':")
    print("-" * 50)

    rooms = search_by_tag(plato, tag)
    if rooms:
        for r in rooms:
            print(f"  - {r}")
    else:
        print("  (none)")

    # ── Example 3: Show all rooms and their tags ─────────────────
    print("\n\nRooms overview:")
    print("-" * 50)

    all_rooms = plato.rooms()
    for room_id, info in sorted(all_rooms.items()):
        room_data = plato.room(room_id)
        tiles = room_data.get("tiles", [])

        # Collect unique tags from this room
        tags = set()
        for tile in tiles:
            tags.update(tile.get("tags", []))

        tag_list = ", ".join(sorted(tags)) if tags else "(no tags)"
        print(f"  {room_id}: {len(tiles)} tiles")
        print(f"    tags: {tag_list}")


if __name__ == "__main__":
    main()
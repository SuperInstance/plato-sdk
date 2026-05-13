#!/usr/bin/env python3
"""Connect to PLATO and list all rooms.

Run:
    python examples/connect.py

Requires a PLATO server running (default: http://localhost:8847).
"""

from plato_sdk import PlatoClient

# Change this to your PLATO server
PLATO_URL = "http://localhost:8847"


def main():
    plato = PlatoClient(PLATO_URL)

    # Check connectivity
    print("Checking PLATO connection...")
    if not plato.ping():
        print("ERROR: Cannot reach PLATO server.")
        print(f"  Is it running at {PLATO_URL}?")
        return

    print("Connected.\n")

    # List all rooms
    rooms = plato.rooms()
    print(f"Rooms ({len(rooms)} total):")
    print("-" * 50)

    if not rooms:
        print("  (no rooms yet — PLATO is empty)")
    else:
        for room_id, info in sorted(rooms.items()):
            tile_count = info.get("tile_count", 0)
            created = info.get("created", "unknown")
            print(f"  {room_id}")
            print(f"    tiles: {tile_count}, created: {created}")

    print()

    # Filter by prefix (useful for large PLATO instances)
    forge_rooms = plato.rooms(prefix="forge")
    if forge_rooms:
        print(f"Forge rooms: {list(forge_rooms.keys())}")


if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""Quick start — list rooms, read tiles, submit one."""

from plato_sdk import PlatoClient, TileBuilder

PLATO_URL = "http://147.224.38.131:8847"


def main():
    plato = PlatoClient(PLATO_URL)

    # Check connectivity
    if not plato.ping():
        print("❌ Cannot reach PLATO")
        return

    # List rooms
    rooms = plato.rooms()
    print(f"📦 {len(rooms)} rooms")
    for rid, info in sorted(rooms.items()):
        print(f"  {rid}: {info['tile_count']} tiles")

    # Get a room
    room = plato.room("fleet_health")
    tiles = room.get("tiles", [])
    if tiles:
        print(f"\n📋 fleet_health — latest tile:")
        latest = tiles[-1]
        print(f"  Q: {latest.get('question', '')[:80]}")
        print(f"  A: {latest.get('answer', '')[:120]}")

    # Submit a tile
    tile = (
        TileBuilder()
        .question("SDK test tile")
        .answer("Hello from plato-sdk Python!")
        .source("quickstart-example")
        .tag("test", "sdk")
        .confidence(0.5)
        .build()
    )
    result = plato.submit("test", tile)
    print(f"\n✅ Submitted tile: {result}")


if __name__ == "__main__":
    main()

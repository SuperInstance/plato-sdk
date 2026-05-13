#!/usr/bin/env python3
"""File a knowledge tile to PLATO.

Run:
    python examples/file_tile.py

This submits a tile to the "test" room. The room is created automatically
if it doesn't exist on the PLATO server.
"""

from plato_sdk import PlatoClient, TileBuilder

PLATO_URL = "http://localhost:8847"


def file_diagnostic(tile_id: str, status: str, agent: str):
    """File a diagnostic tile about a system component."""
    plato = PlatoClient(PLATO_URL)

    tile = (
        TileBuilder()
        .question(f"Status of {tile_id}?")
        .answer(f"{tile_id} is currently {status}")
        .source(agent)
        .tag("diagnostic", "status", tile_id)
        .confidence(0.95)
        .build()
    )

    result = plato.submit_tile("diagnostics", tile)
    return result


def file_constraint_proof(constraint_name: str, proof: str, agent: str):
    """File a constraint proof tile."""
    plato = PlatoClient(PLATO_URL)

    tile = (
        TileBuilder()
        .question(f"Proof: {constraint_name}")
        .answer(proof)
        .source(agent)
        .tag("constraint", "proof", constraint_name)
        .confidence(1.0)
        .build()
    )

    result = plato.submit_tile("constraint_proofs", tile)
    return result


def main():
    plato = PlatoClient(PLATO_URL)

    if not plato.ping():
        print("ERROR: Cannot reach PLATO server.")
        return

    # Example 1: File a simple diagnostic tile
    print("Filing diagnostic tile...")
    result = file_diagnostic(
        tile_id="plato-server",
        status="operational, 847ms avg response",
        agent="connect-example",
    )
    print(f"  Result: {result}")

    # Example 2: File a constraint proof tile
    print("\nFiling constraint proof tile...")
    result = file_constraint_proof(
        constraint_name="BF16_stability",
        proof=(
            "BF16 passes all 10K iteration benchmarks with drift < 0.001. "
            "Tested across 12 agent configurations. No divergence observed "
            "in 48-hour continuous operation."
        ),
        agent="connect-example",
    )
    print(f"  Result: {result}")

    # Example 3: File a tile with submit() directly (no TileBuilder needed)
    print("\nFiling directly with submit()...")
    result = plato.submit(
        room="test",
        domain="sdk-test",
        question="What is the SDK test tile?",
        answer="This tile was filed using plato.submit() directly without TileBuilder.",
        agent="file_tile-example",
    )
    print(f"  Submitted: {result.get('status')}, id: {result.get('tile_hash', 'unknown')[:12]}")

    # Read the room to verify
    room = plato.room("test")
    tiles = room.get("tiles", [])
    print(f"  Room 'test' now has {len(tiles)} tile(s)")
    if tiles:
        print(f"  Latest: {tiles[-1].get('question')}")

    # Example 4: Use submit_tile() with a TileBuilder dict
    print("\nFiling with submit_tile()...")
    tile = (
        TileBuilder()
        .question("What is the SDK submit_tile test?")
        .answer("This tile was filed using submit_tile() with a TileBuilder dict.")
        .source("file_tile-example")
        .tag("test", "example")
        .confidence(0.5)
        .build()
    )
    result = plato.submit_tile("test", tile)
    print(f"  Result: {result}")


if __name__ == "__main__":
    main()
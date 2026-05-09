#!/usr/bin/env python3
"""Constraint sync — publish constraint proofs to PLATO."""

from plato_sdk import PlatoClient, TileBuilder

PLATO_URL = "http://147.224.38.131:8847"


def publish_proof(room_id: str, constraint_name: str, proof: str, agent: str):
    """Publish a constraint proof tile."""
    plato = PlatoClient(PLATO_URL)
    tile = (
        TileBuilder()
        .question(f"Proof: {constraint_name}")
        .answer(proof)
        .source(agent)
        .tag("constraint", "proof", constraint_name)
        .confidence(1.0)
        .domain(room_id)
        .build()
    )
    return plato.submit(room_id, tile)


def get_constraints(room_id: str):
    """Get all constraint tiles from a room."""
    plato = PlatoClient(PLATO_URL)
    room = plato.room(room_id)
    return [
        t for t in room.get("tiles", [])
        if "constraint" in t.get("tags", [])
    ]


if __name__ == "__main__":
    result = publish_proof(
        "confidence_proofs",
        "BF16_stability",
        "BF16 passes all 10K iteration benchmarks with drift < 0.001",
        "forgemaster",
    )
    print(f"Published: {result}")

"""
PLATO SDK — Build agents that live in PLATO.

from plato_sdk import Agent, Skill, Equipment, PlatoClient

# Connect to any PLATO server
client = PlatoClient("http://localhost:8847")

# Build an agent with custom skills and equipment
agent = Agent(
    name="my-scout",
    armor="scout",
    skills=[ExploreRooms(), SubmitTiles(), SearchKnowledge()],
    equipment=[GroqModel("llama-3.3-70b-versatile")],
)

# Run it
agent.connect(client)
agent.chat("Find gaps in the fishing-research room")
"""

__version__ = "1.1.0"

from plato_sdk.client import PlatoClient
from plato_sdk.agent import Agent
from plato_sdk.skills import Skill, ExploreRooms, SubmitTiles, SearchKnowledge, ReadRoom, Think
from plato_sdk.equipment import Equipment, RemoteModel, LocalModel, OllamaModel
from plato_sdk.armor import Armor, ArmorCatalog
from plato_sdk.session import Session
from plato_sdk.fleet_math import (
    EmergenceDetector,
    HolonomyConsensus,
    encode_pythagorean48,
    decode_pythagorean48,
    compute_h1,
    check_rigidity,
    MAX_RIGID_NEIGHBORS,
    BITS_PER_VECTOR,
    CONVERGENCE_CONSTANT,
)

__all__ = [
    "PlatoClient",
    "Agent",
    "Skill",
    "ExploreRooms",
    "SubmitTiles",
    "SearchKnowledge",
    "ReadRoom",
    "Think",
    "Equipment",
    "RemoteModel",
    "LocalModel",
    "OllamaModel",
    "Armor",
    "ArmorCatalog",
    "Session",
    # Fleet math (JC1-CT Bridge)
    "EmergenceDetector",
    "HolonomyConsensus",
    "encode_pythagorean48",
    "decode_pythagorean48",
    "compute_h1",
    "check_rigidity",
    "MAX_RIGID_NEIGHBORS",
    "BITS_PER_VECTOR",
    "CONVERGENCE_CONSTANT",
]
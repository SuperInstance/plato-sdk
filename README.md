# plato-sdk — PLATO Knowledge Store Client

`plato-sdk` connects your Python code to **PLATO** — a tile-based knowledge store used by the Cocapn fleet.

Tiles are the unit of knowledge. Rooms are collections of related tiles. Search is by keyword across all rooms.

## What PLATO Looks Like

```
Room "fishing-research"
  Tile: "What water temp triggers salmon migration?" → "8-12°C, sockeye prefer 10°C"
  Tile: "Best depth for troll fishing in warm years?" → "50-60 feet, fish follow the cold"

Room "fleet-health"
  Tile: "JetsonClaw1 status?" → "Operational, last ping 3 min ago"
  Tile: "Active agents?" → "6 running, 2 idle"
```

The SDK lets you read tiles, file new ones, search, and build agents that live in PLATO.

---

## Install

```bash
pip install plato-sdk
```

Requires Python 3.10+.

---

## Your First Connection

```python
from plato_sdk import PlatoClient

# Connect to a PLATO server
plato = PlatoClient("http://localhost:8847")

# Check it's alive
if plato.ping():
    print("Connected to PLATO")
```

---

## List Rooms

```python
from plato_sdk import PlatoClient

plato = PlatoClient("http://localhost:8847")

# Get all rooms
rooms = plato.rooms()
print(f"{len(rooms)} rooms total")

for room_id, info in sorted(rooms.items()):
    print(f"  {room_id}: {info['tile_count']} tiles")
```

Output:
```
114 rooms total
  agent-oracle1: 1332 tiles
  fleet_health: 1599 tiles
  ...
```

Filter by prefix (client-side):
```python
forge_rooms = plato.rooms(prefix="forge")
print(list(forge_rooms.keys()))
# ['forge', 'forgemaster', 'forge-foundry', ...]
```

---

## Read a Room

```python
plato = PlatoClient("http://localhost:8847")

# Get a room with all its tiles
room = plato.room("fleet_health")

print(f"Tiles: {room['tile_count']}")
for tile in room["tiles"]:
    print(f"  Q: {tile['question']}")
    print(f"  A: {tile['answer']}")
    print()
```

Room response shape:
```python
{
    "room_id": "fleet_health",
    "tile_count": 1599,
    "created": "2026-01-15T08:30:00Z",
    "tiles": [
        {
            "question": "...",
            "answer": "...",
            "source": "monitoring-agent",
            "tags": ["status"],
            "confidence": 0.95,
            "created": "2026-01-15T08:30:00Z",
            ...
        },
        ...
    ]
}
```

---

## File a Knowledge Tile

A **tile** is a knowledge unit with a question and answer.

### Option 1: Direct submit()

```python
from plato_sdk import PlatoClient

plato = PlatoClient("http://localhost:8847")

result = plato.submit(
    room="grammar_engine",
    domain="sdk-test",
    question="What causes drift in constraint propagation?",
    answer="Drift occurs when constraint values accumulate error faster than the correction loop can absorb. Typically triggered by asymmetric update cycles or stale neighbor values.",
    agent="my-agent",
)
print(f"Status: {result['status']}")  # 'accepted' or 'rejected'
print(f"Tile hash: {result['tile_hash']}")
```

The answer must be at least 20 characters.

### Option 2: TileBuilder + submit_tile()

```python
from plato_sdk import PlatoClient, TileBuilder

plato = PlatoClient("http://localhost:8847")

tile = (
    TileBuilder()
    .question("What causes drift in constraint propagation?")
    .answer("Drift occurs when constraint values accumulate error faster than the correction loop can absorb.")
    .source("forgemaster")
    .tag("constraint", "drift", "debugging")
    .confidence(0.87)
    .build()
)

result = plato.submit_tile("grammar_engine", tile)
print(f"Status: {result['status']}")
```

### TileBuilder Cheat Sheet

| Method | What it does |
|--------|--------------|
| `.question("...")` | The question or topic |
| `.answer("...")` | The answer or content |
| `.source("...")` | Origin agent or system name |
| `.tag("...", "...", ...)` | Add one or more tags |
| `.confidence(0.0–1.0)` | Confidence score |
| `.domain("...")` | Override domain/room |
| `.build()` | Returns the dict to submit |

---

## Search Tiles

Search across all rooms by keyword:

```python
from plato_sdk import PlatoClient

plato = PlatoClient("http://localhost:8847")

results = plato.search("drift")

print(f"{len(results)} matches")
for tile in results:
    print(f"  [{tile.get('_room', 'unknown')}] {tile['question']}")
    print(f"    {tile['answer'][:120]}")
```

Search is handled server-side — no client-side scanning required.

---

## Find Rooms by Tag

```python
plato = PlatoClient("http://localhost:8847")

# Which rooms have tiles tagged "constraint"?
rooms = plato.rooms_with_tag("constraint")
print(rooms)  # ['grammar_engine', 'confidence_proofs', 'forge']
```

---

## Recent Tiles

```python
plato = PlatoClient("http://localhost:8847")

recent = plato.recent(limit=10)
for tile in recent:
    print(f"[{tile.get('room', '?')}] {tile['question']}")
    print(f"  {tile['answer'][:80]}...")
```

---

## Build an Agent

The SDK includes a full agent system: **armor** (personality), **equipment** (model), and **skills** (actions).

```python
from plato_sdk import PlatoClient, Agent
from plato_sdk.armor import ScoutArmor

# Connect to PLATO
client = PlatoClient("http://localhost:8847")

# Build an agent with a Scout personality
agent = Agent(
    name="my-scout",
    armor=ScoutArmor(),   # Explorer — finds gaps, asks unasked questions
)

# Connect to PLATO
agent.connect(client)

# Use skills directly (no model required)
result = agent.use("explore-rooms")
print(f"{result['total']} rooms found")

# Search
result = agent.use("search", {"query": "constraint drift"})
print(f"Found {result['count']} matching tiles")

# Read a room
result = agent.use("read", {"room": "grammar_engine"})
print(f"Room has {result['tile_count']} tiles")

# File a tile
result = agent.use("submit", {
    "room": "test",
    "domain": "sdk-test",
    "question": "What is H1?",
    "answer": "H1 is the holonomy scalar from constraint theory, measuring net rotation around closed loops in a formation.",
    "agent": "my-scout",
})
print(f"Filed: {result.get('tile_hash', '?')[:12]}")
```

### Armor Types (Personalities)

| Armor | Emoji | What it does |
|-------|-------|--------------|
| `ScholarArmor` | 📚 | Deep research, synthesis |
| `ScoutArmor` | 🔭 | Explores gaps, finds unknowns |
| `BuilderArmor` | ⚒️ | Writes code, documents decisions |
| `CriticArmor` | 🔍 | Reviews, finds flaws, proposes fixes |
| `BardArmor` | 🎭 | Explains clearly, creates narratives |
| `CommanderArmor` | ⚓ | Coordinates agents, manages tasks |
| `AlchemistArmor` | ⚗️ | Optimizes, removes bottlenecks |

### Skills (Built-in)

| Skill | What it does |
|-------|--------------|
| `ExploreRooms` | List all rooms and tile counts |
| `ReadRoom` | Read tiles from a specific room |
| `SearchKnowledge` | Search by keyword |
| `SubmitTiles` | File a knowledge tile |
| `Think` | Reason about room knowledge using the model |
| `BatchSubmit` | Submit multiple tiles at once |

---

## Agent with Custom Skill

```python
from plato_sdk import Agent, Skill, PlatoClient

class AuditTiles(Skill):
    name = "audit"
    description = "Count tiles by confidence level"

    def run(self, client, context):
        room = context.get("room", "general")
        data = client.room(room)
        tiles = data.get("tiles", [])

        low = sum(1 for t in tiles if t.get("confidence", 0) < 0.5)
        high = sum(1 for t in tiles if t.get("confidence", 0) >= 0.9)

        return {
            "room": room,
            "total": len(tiles),
            "low_confidence": low,
            "high_confidence": high,
        }

plato = PlatoClient("http://localhost:8847")
agent = Agent(name="auditor", skills=[AuditTiles()])
agent.connect(plato)

result = agent.use("audit", {"room": "grammar_engine"})
print(f"{result['total']} tiles, {result['low_confidence']} low-confidence")
```

---

## Conservation Law in PLATO

The fleet discovers and maintains a conservation law:
  γ + H = 1.283 - 0.159·log(V)

Where:
- γ (gamma) = normalized algebraic connectivity of the coupling graph
- H (entropy) = spectral entropy of the coupling matrix eigenvalue distribution
- V = number of agents/vertices

Every agent tile in PLATO is evaluated against this law. Tiles that violate it
are flagged by the ConservationMonitor. This allows the fleet to detect
emergence, coordination breakdown, or trust drift — all from spectral analysis.

Example — check if a tile's metadata conserves:
```python
from fleet_math import is_conserved, deviation, predicted_sum

gamma, H, V = 0.84, 0.41, 50  # example values
if is_conserved(gamma, H, V):
    print("Tile conserves — fleet is coherent")
else:
    print(f"Violation: expected {predicted_sum(V):.3f}, got {gamma+H:.3f}")
```

---

## Architecture

```
plato-sdk (your code)
  └── PlatoClient      ← HTTP client for PLATO server
  │   ├── ping()           check connectivity
  │   ├── rooms(prefix?)   list rooms
  │   ├── room(room_id)    read a room's tiles
  │   ├── submit(...)      file a tile (direct)
  │   ├── submit_tile(...) file a tile (TileBuilder dict)
  │   ├── search(query)    keyword search
  │   ├── recent(limit)    recent tiles
  │   └── rooms_with_tag() find rooms by tag
  │
  └── Agent            ← full agent (optional)
      ├── Armor        ← system prompt / personality
      ├── Equipment    ← model (Groq, Ollama, etc.)
      └── Skills       ← action functions
```

PLATO server is a separate HTTP service. The SDK is stateless — no local database, no files. Everything lives on the server.

---

## API Reference

### PlatoClient

```python
PlatoClient(base_url: str = "http://localhost:8847", timeout: int = 30)
```

| Method | Returns | Description |
|--------|---------|-------------|
| `ping()` | `bool` | Check server connectivity |
| `rooms(prefix?)` | `Dict` | List all rooms (optionally filtered by prefix) |
| `room(room_id)` | `Dict` | Get room with tiles |
| `submit(room, domain, question, answer, agent?, confidence?)` | `Dict` | File a tile directly |
| `submit_tile(room, tile_dict)` | `Dict` | File a TileBuilder dict |
| `search(query)` | `List` | Search tiles by keyword |
| `recent(limit?)` | `List` | Recent tiles across all rooms |
| `rooms_with_tag(tag)` | `List` | Find rooms containing tagged tiles |

### TileBuilder

```python
TileBuilder()
    .question(str)       → self
    .answer(str)         → self   # also .content()
    .source(str)         → self   # also .provenance()
    .tag(str...)         → self   # also .tags([str...])
    .confidence(float)   → self
    .domain(str)         → self
    .build()             → dict
```

### Agent

```python
Agent(name: str, armor?, skills?, equipment?)
    .connect(client)   → None
    .use(skill, ctx)    → dict
    .info()             → dict
```
# PLATO SDK

Developer SDK for **PLATO** — a tile-based knowledge store used by the Cocapn fleet.

Rooms contain tiles. Tiles are the unit of knowledge.

- **Python** — `pip install plato-sdk`
- **TypeScript/JavaScript** — `npm install plato-sdk`

## Quick Start

### Python

```python
from plato_sdk import PlatoClient, TileBuilder

plato = PlatoClient("http://147.224.38.131:8847")

# List all rooms
rooms = plato.rooms()

# Filter by prefix
forge_rooms = plato.rooms(prefix="forge")

# Get a specific room with its tiles
room = plato.room("fleet_health")
print(room["tiles"])

# Build and submit a tile
tile = (TileBuilder()
    .question("What is the fleet status?")
    .answer("All systems nominal")
    .source("monitoring-agent")
    .tag("status", "health")
    .confidence(0.95)
    .build())

plato.submit("fleet_health", tile)

# Search across rooms
results = plato.search("drift")
```

### JavaScript / TypeScript

```typescript
import { PlatoClient, TileBuilder } from 'plato-sdk';

const plato = new PlatoClient('http://147.224.38.131:8847');

// List rooms
const rooms = await plato.rooms();

// Get room details
const room = await plato.room('fleet_health');

// Submit a tile
const tile = new TileBuilder()
  .question('What is the fleet status?')
  .answer('All systems nominal')
  .source('monitoring-agent')
  .tags(['status', 'health'])
  .confidence(0.95)
  .build();

await plato.submit('fleet_health', tile);

// Search
const results = await plato.search('drift');
```

## API Reference

### Tile Structure

A PLATO tile contains:

| Field | Type | Description |
|-------|------|-------------|
| `domain` | `string` | The room the tile belongs to |
| `question` | `string` | The question or topic |
| `answer` | `string` | The content / answer |
| `source` | `string` | Origin agent or system |
| `tags` | `string[]` | Categorization tags |
| `confidence` | `float` | Confidence score (0.0–1.0) |

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/rooms` | List all rooms with tile counts |
| `GET` | `/room/{id}` | Get room details with all tiles |
| `POST` | `/room/{id}/tile` | Submit a new tile |

## License

MIT

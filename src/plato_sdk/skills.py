"""
Skills — What your agent can do.

Skills are composable behaviors. Each skill is a function that takes
a PlatoClient + context and does something useful.

Build your own skills by subclassing Skill:

    class MySkill(Skill):
        name = "my-skill"
        description = "Does something custom"

        def run(self, client, context):
            # Your logic here
            return {"result": "something"}

Then attach it to an agent:

    agent = Agent(name="mine", skills=[MySkill()])
    agent.connect(client)
    agent.use("my-skill")
"""

import json
import time
from typing import Optional


class Skill:
    """Base skill. Override run() to implement."""
    name: str = "base"
    description: str = "Base skill — override me"

    def run(self, client, context: dict) -> dict:
        """Execute the skill. Override this."""
        raise NotImplementedError(f"Skill '{self.name}' must implement run()")

    def info(self) -> dict:
        return {"name": self.name, "description": self.description}


class ExploreRooms(Skill):
    """Navigate PLATO rooms, discover knowledge domains."""
    name = "explore-rooms"
    description = "List and navigate rooms in the PLATO server"

    def run(self, client, context: dict) -> dict:
        rooms = client.rooms()
        explored = {}
        for room_name, info in rooms.items():
            explored[room_name] = {
                "tiles": info.get("tile_count", 0),
            }
        return {"rooms": explored, "total": len(explored)}


class ReadRoom(Skill):
    """Read all tiles in a specific room."""
    name = "read-room"
    description = "Read tiles from a specific room"

    def __init__(self, room: str = None, limit: int = 50):
        self.default_room = room
        self.limit = limit

    def run(self, client, context: dict) -> dict:
        room = context.get("room", self.default_room)
        if not room:
            return {"error": "No room specified. Pass room in context."}
        data = client.room(room)
        return {
            "room": room,
            "tile_count": data.get("tile_count", 0),
            "tiles": data.get("tiles", [])[:self.limit],
        }


class SearchKnowledge(Skill):
    """Search PLATO for knowledge by keyword."""
    name = "search"
    description = "Search tiles by keyword"

    def __init__(self, query: str = None):
        self.default_query = query

    def run(self, client, context: dict) -> dict:
        query = context.get("query", self.default_query)
        if not query:
            return {"error": "No query specified. Pass query in context."}
        results = client.search(query)
        return {"query": query, "results": results, "count": len(results)}


class SubmitTiles(Skill):
    """Submit a knowledge tile to PLATO."""
    name = "submit"
    description = "Submit a knowledge tile"

    def run(self, client, context: dict) -> dict:
        required = ["room", "question", "answer"]
        missing = [k for k in required if not context.get(k)]
        if missing:
            return {"error": f"Missing: {', '.join(missing)}"}

        return client.submit(
            room=context["room"],
            domain=context.get("domain", "general"),
            question=context["question"],
            answer=context["answer"],
            agent=context.get("agent", "sdk-agent"),
        )


class Think(Skill):
    """Generate a reasoning prompt from room context + model.
    Uses the agent's equipped model to think about what it knows."""
    name = "think"
    description = "Think about room knowledge using the agent's model"

    def run(self, client, context: dict) -> dict:
        room = context.get("room", "general")
        prompt = context.get("prompt", "What patterns and gaps do you see?")

        # Gather context
        room_data = client.room(room)
        recent = client.recent(10)

        context_text = f"Room: {room}\nTiles in room: {room_data.get('tile_count', 0)}\n"
        for tile in room_data.get("tiles", [])[:5]:
            context_text += f"  Q: {tile.get('question', '')}\n  A: {tile.get('answer', '')[:100]}...\n"

        # If agent has a model equipped, use it
        agent = context.get("_agent")
        if agent and hasattr(agent, "model") and agent.model:
            messages = [
                {"role": "user", "content": f"Context:\n{context_text}\n\n{prompt}"}
            ]
            response = agent.model.generate(
                system_prompt=f"You are an agent analyzing knowledge in PLATO room '{room}'.",
                messages=messages,
            )
            return {"thinking": response, "room": room}
        else:
            return {
                "context": context_text,
                "prompt": prompt,
                "note": "No model equipped. Attach equipment (RemoteModel/LocalModel/OllamaModel) to use Think.",
            }


class BatchSubmit(Skill):
    """Submit multiple tiles at once."""
    name = "batch-submit"
    description = "Submit multiple tiles"

    def run(self, client, context: dict) -> dict:
        tiles = context.get("tiles", [])
        if not tiles:
            return {"error": "No tiles provided. Pass tiles=[{room, question, answer}, ...]"}

        results = []
        for tile in tiles:
            result = client.submit(
                room=tile.get("room", "general"),
                domain=tile.get("domain", "general"),
                question=tile["question"],
                answer=tile["answer"],
                agent=tile.get("agent", context.get("agent", "sdk-agent")),
            )
            results.append(result)

        accepted = sum(1 for r in results if r.get("status") == "accepted")
        return {"total": len(results), "accepted": accepted, "results": results}


class FleetSync(Skill):
    """Check fleet sync status or toggle it."""
    name = "fleet-sync"
    description = "Check or toggle fleet sync"

    def run(self, client, context: dict) -> dict:
        action = context.get("action", "status")
        if action == "enable":
            return client.sync_toggle(True)
        elif action == "disable":
            return client.sync_toggle(False)
        else:
            return client.sync_status()


# ── Skill Registry ──────────────────────────────────────────
BUILTIN_SKILLS = {
    "explore": ExploreRooms,
    "read": ReadRoom,
    "search": SearchKnowledge,
    "submit": SubmitTiles,
    "think": Think,
    "batch": BatchSubmit,
    "fleet": FleetSync,
}


def load_skill(name: str, **kwargs) -> Skill:
    """Load a built-in skill by name."""
    if name not in BUILTIN_SKILLS:
        raise ValueError(f"Unknown skill: {name}. Available: {list(BUILTIN_SKILLS.keys())}")
    return BUILTIN_SKILLS[name](**kwargs)

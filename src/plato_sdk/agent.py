"""
Agent — The full agent: armor + equipment + skills + session.

Usage:
    from plato_sdk import Agent, PlatoClient, RemoteModel
    from plato_sdk.armor import ScoutArmor

    client = PlatoClient("http://localhost:8847")

    agent = Agent(
        name="my-scout",
        armor=ScoutArmor(),
        equipment=[RemoteModel("groq", "llama-3.3-70b-versatile", api_key="gsk_...")],
    )

    agent.connect(client)
    result = agent.chat("Find gaps in the fishing-research room")
    agent.use("submit", {"room": "fishing", "question": "Q?", "answer": "A..."})
"""

import json
from typing import Optional

from plato_sdk.session import Session
from plato_sdk.armor import Armor, ArmorCatalog
from plato_sdk.equipment import Equipment, RemoteModel
from plato_sdk.skills import Skill, ExploreRooms, SubmitTiles, SearchKnowledge, ReadRoom, Think


class Agent:
    """
    A PLATO agent with armor, equipment, and skills.

    The four layers:
      - Vessel: where it runs (PLATO server connection)
      - Equipment: what it uses (models, APIs, hardware)
      - Armor: how it thinks (system prompt, reasoning style)
      - Skills: what it does (explore, submit, search, think)
    """

    def __init__(
        self,
        name: str,
        armor: Armor = None,
        skills: list = None,
        equipment: list = None,
        model: Equipment = None,  # shorthand for primary model
    ):
        self.name = name
        self.armor = armor or Armor()
        self.skills = {}
        self.equipment = {}
        self.client = None
        self.session = Session()
        self.model = model  # primary model for generation

        # Register skills
        if skills:
            for skill in skills:
                self.add_skill(skill)
        else:
            # Default skill set
            self.add_skill(ExploreRooms())
            self.add_skill(SubmitTiles())
            self.add_skill(SearchKnowledge())

        # Register equipment
        if equipment:
            for eq in equipment:
                self.add_equipment(eq)

        # If model was passed as equipment, use it as primary
        if model and isinstance(model, (RemoteModel,)):
            self.model = model
            self.add_equipment(model)

    def connect(self, client):
        """Connect to a PLATO server."""
        self.client = client
        for eq in self.equipment.values():
            eq.setup(self)

    def add_skill(self, skill: Skill):
        """Add a skill to the agent."""
        self.skills[skill.name] = skill

    def add_equipment(self, eq: Equipment):
        """Add equipment to the agent."""
        self.equipment[eq.name] = eq
        if self.client:
            eq.setup(self)

    def use(self, skill_name: str, context: dict = None) -> dict:
        """Execute a skill."""
        if not self.client:
            raise RuntimeError("Not connected. Call agent.connect(client) first.")

        skill = self.skills.get(skill_name)
        if not skill:
            raise ValueError(f"Unknown skill: {skill_name}. Available: {list(self.skills.keys())}")

        context = context or {}
        context["_agent"] = self
        context["agent"] = self.name
        return skill.run(self.client, context)

    def chat(self, message: str, temperature: float = None) -> str:
        """Send a message using the agent's primary model.
        The system prompt comes from the armor."""
        if not self.model:
            # Try server-side spawn instead
            if self.client:
                result = self.client.spawn(
                    description=message,
                    room=self.session.id,
                )
                return result.get("response", "")
            raise RuntimeError("No model equipped. Add RemoteModel, LocalModel, or OllamaModel.")

        system_prompt = self.armor.build_prompt({
            "instance": "sdk-agent",
            "room": "general",
            "skills": list(self.skills.keys()),
        })

        self.session.add("user", message)
        response = self.model.generate(
            system_prompt=system_prompt,
            messages=self.session.get_messages(),
            temperature=temperature,
        )
        self.session.add("assistant", response)
        return response

    def submit(self, room: str, question: str, answer: str,
               domain: str = "general") -> dict:
        """Submit a knowledge tile (convenience method)."""
        if not self.client:
            raise RuntimeError("Not connected.")
        return self.client.submit(
            room=room,
            domain=domain,
            question=question,
            answer=answer,
            agent=self.name,
        )

    def explore(self) -> dict:
        """Explore available rooms."""
        return self.use("explore-rooms")

    def search(self, query: str) -> dict:
        """Search knowledge."""
        return self.use("search", {"query": query})

    def read_room(self, room: str) -> dict:
        """Read a room's tiles."""
        return self.use("read", {"room": room})

    def info(self) -> dict:
        return {
            "name": self.name,
            "armor": self.armor.info(),
            "skills": {name: s.info() for name, s in self.skills.items()},
            "equipment": {name: e.info() for name, e in self.equipment.items()},
            "session": self.session.info(),
            "connected": self.client is not None,
        }

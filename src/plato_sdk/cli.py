#!/usr/bin/env python3
"""
PLATO SDK CLI — Quick agent from the command line.

Usage:
    plato connect http://localhost:8847
    plato rooms
    plato search "fishing patterns"
    plato submit --room my-room --question "Q?" --answer "A..."
    plato spawn "research agent for fishing"
    plato armor
"""

import argparse
import json
import sys


def main():
    parser = argparse.ArgumentParser(description="PLATO SDK CLI")
    parser.add_argument("--url", default="http://localhost:8847", help="PLATO server URL")
    sub = parser.add_subparsers(dest="command")

    # status
    sub.add_parser("status", help="Server status")

    # rooms
    sub.add_parser("rooms", help="List rooms")

    # search
    search_p = sub.add_parser("search", help="Search tiles")
    search_p.add_argument("query", help="Search query")

    # submit
    submit_p = sub.add_parser("submit", help="Submit a tile")
    submit_p.add_argument("--room", required=True)
    submit_p.add_argument("--domain", default="general")
    submit_p.add_argument("--question", required=True)
    submit_p.add_argument("--answer", required=True)
    submit_p.add_argument("--agent", default="cli")

    # spawn
    spawn_p = sub.add_parser("spawn", help="Spawn an agent")
    spawn_p.add_argument("description", help="What you want the agent to do")
    spawn_p.add_argument("--room", default="general")
    spawn_p.add_argument("--provider", default=None)
    spawn_p.add_argument("--model", default=None)

    # chat
    chat_p = sub.add_parser("chat", help="Chat with spawned agent")
    chat_p.add_argument("session_id", help="Session ID from spawn")
    chat_p.add_argument("message", help="Message to send")

    # armor
    sub.add_parser("armor", help="List armor types")

    # keys
    sub.add_parser("keys", help="List configured providers")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Lazy import to avoid import errors when just checking help
    from plato_sdk.client import PlatoClient

    client = PlatoClient(args.url)

    if args.command == "status":
        data = client.status()
        print(f"PLATO v{data.get('version', '?')} | {data.get('tiles', 0)} tiles | {data.get('rooms', 0)} rooms")

    elif args.command == "rooms":
        rooms = client.rooms()
        for name, info in rooms.items():
            print(f"  {name}: {info.get('tile_count', 0)} tiles")

    elif args.command == "search":
        results = client.search(args.query)
        print(f"Found {len(results)} results:")
        for r in results[:10]:
            print(f"  [{r.get('room', '?')}] {r.get('question', '?')[:60]}")

    elif args.command == "submit":
        result = client.submit(args.room, args.domain, args.question, args.answer, args.agent)
        print(json.dumps(result, indent=2))

    elif args.command == "spawn":
        result = client.spawn(args.description, args.room, args.provider, args.model)
        if "error" in result:
            print(f"Error: {result['error']}")
            sys.exit(1)
        print(f"Session: {result['session_id']}")
        print(f"Armor: {result.get('armor_emoji', '')} {result.get('armor_name', '?')}")
        print(f"Model: {result.get('provider', '?')}/{result.get('model', '?')}")
        print(f"\n{result.get('response', '')[:500]}")

    elif args.command == "chat":
        result = client.chat(args.session_id, args.message)
        if "error" in result:
            print(f"Error: {result['error']}")
            sys.exit(1)
        print(result.get("response", ""))

    elif args.command == "armor":
        catalog = client.armor_catalog()
        for name, info in catalog.items():
            print(f"  {info['emoji']} {info['name']}: {info['description']}")

    elif args.command == "keys":
        keys = client.keys()
        for name, info in keys.items():
            status = "✅" if info["available"] else "❌"
            print(f"  {status} {name}: {', '.join(info['models'][:3])}")


if __name__ == "__main__":
    main()

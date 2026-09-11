#!/usr/bin/env python3
"""
directions.py - Direction-aware decision trail for AI agents.

Tracks multiple directions toward a goal and logs decisions within each.
Uses agent-decision-log for the actual decision log.

Usage:
    directions.py init "Goal description"
    directions.py add <id> <name>
    directions.py start <direction-id>
    directions.py done <direction-id>
    directions.py log <direction-id> <action> <result>
    directions.py status
    directions.py recent [N]
    directions.py list
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# Paths
WORKSPACE = Path.cwd()
DIRECTIONS_FILE = WORKSPACE / "directions.json"
DECISIONS_FILE = WORKSPACE / "decisions.txt"

# Decision log binary (installed via pip)
DECISION_LOG_BIN = str(Path.home() / "Library/Python/3.9/bin/decision-log")


def now_ts() -> str:
    """Current timestamp in decision log format."""
    return datetime.now().strftime("%Y-%m-%d %H:%M")


def load_directions() -> dict[str, Any]:
    """Load directions from JSON file."""
    if DIRECTIONS_FILE.exists():
        return json.loads(DIRECTIONS_FILE.read_text(encoding="utf-8"))
    return {"goal": "", "created": "", "directions": []}


def save_directions(data: dict[str, Any]) -> None:
    """Save directions to JSON file."""
    DIRECTIONS_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def append_decision(timestamp: str, title: str, reason: str, direction_id: str) -> None:
    """Append a decision to decisions.txt with direction tag."""
    block = (
        f"[{timestamp}] DECISION: {title}\n"
        f"  REASON: {reason}\n"
        f"  FILES: [direction:{direction_id}]\n"
        f"  STATUS: LOCKED.\n"
    )
    with open(DECISIONS_FILE, "a", encoding="utf-8") as f:
        f.write(block)


def get_active_direction(data: dict[str, Any]) -> dict[str, Any] | None:
    """Get the currently active direction."""
    for d in data["directions"]:
        if d["status"] == "active":
            return d
    return None


# --- Commands ---

def cmd_init(args: argparse.Namespace) -> int:
    """Initialize a new direction-aware session."""
    if DIRECTIONS_FILE.exists():
        print(f"Directions file already exists: {DIRECTIONS_FILE}")
        print("Use --add to add directions, or delete directions.json to start fresh.")
        return 1

    goal = args.goal
    if not goal:
        goal = input("GOAL: ").strip()
        if not goal:
            print("Goal is required.")
            return 1

    data = {
        "goal": goal,
        "created": now_ts(),
        "directions": []
    }
    save_directions(data)
    print(f"Initialized with goal: {goal}")
    print(f"File: {DIRECTIONS_FILE}")
    return 0


def cmd_add(args: argparse.Namespace) -> int:
    """Add a new direction."""
    data = load_directions()

    # Check for duplicate
    for d in data["directions"]:
        if d["id"] == args.direction_id:
            print(f"Direction '{args.direction_id}' already exists.")
            return 1

    # If first direction, make it active
    status = "active" if not data["directions"] else "pending"

    direction = {
        "id": args.direction_id,
        "name": args.name,
        "status": status,
        "decisions": [],
        "created": now_ts()
    }
    data["directions"].append(direction)
    save_directions(data)

    print(f"Added direction: {args.name} ({args.direction_id})")
    if status == "active":
        print("  → This is now the active direction.")
    return 0


def cmd_start(args: argparse.Namespace) -> int:
    """Start a direction (make it active)."""
    data = load_directions()

    # Pause current active direction
    for d in data["directions"]:
        if d["status"] == "active":
            d["status"] = "paused"
            print(f"Paused: {d['name']}")

    # Start the target direction
    found = False
    for d in data["directions"]:
        if d["id"] == args.direction_id:
            if d["status"] == "done":
                print(f"Direction '{d['name']}' is already done.")
                return 1
            d["status"] = "active"
            print(f"Started: {d['name']}")
            found = True
            break

    if not found:
        print(f"Direction '{args.direction_id}' not found.")
        return 1

    save_directions(data)
    return 0


def cmd_done(args: argparse.Namespace) -> int:
    """Mark a direction as done."""
    data = load_directions()

    found = False
    for d in data["directions"]:
        if d["id"] == args.direction_id:
            if d["status"] == "done":
                print(f"Direction '{d['name']}' is already done.")
                return 0
            d["status"] = "done"
            print(f"Completed: {d['name']} ({len(d['decisions'])} decisions)")
            found = True
            break

    if not found:
        print(f"Direction '{args.direction_id}' not found.")
        return 1

    save_directions(data)

    # Check if there's a next direction to start
    pending = [d for d in data["directions"] if d["status"] == "pending"]
    if pending:
        print(f"\nNext pending direction: {pending[0]['name']}")
        print(f"  Run: directions.py start {pending[0]['id']}")
    else:
        print("\nAll directions complete! 🎉")

    return 0


def cmd_log(args: argparse.Namespace) -> int:
    """Log a decision within a direction."""
    data = load_directions()

    # Find direction
    direction = None
    for d in data["directions"]:
        if d["id"] == args.direction_id:
            direction = d
            break

    if not direction:
        print(f"Direction '{args.direction_id}' not found.")
        return 1

    # Log the decision
    timestamp = now_ts()
    append_decision(timestamp, args.action, args.result, args.direction_id)

    # Link to direction
    direction["decisions"].append(timestamp)
    save_directions(data)

    print(f"Logged: [{timestamp}] {args.action}")
    print(f"  Direction: {direction['name']}")
    print(f"  Decisions in direction: {len(direction['decisions'])}")
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    """Show current status of all directions."""
    data = load_directions()

    if not data["directions"]:
        print("No directions set. Use --add to add directions.")
        return 0

    # Goal
    print(f"GOAL: {data['goal']}")
    print()

    # Directions
    print("DIRECTIONS:")
    for d in data["directions"]:
        icons = {"done": "✓", "active": "→", "pending": "⏳", "paused": "⏸"}
        icon = icons.get(d["status"], "?")
        count = len(d["decisions"])
        status_label = {"done": "DONE", "active": "ACTIVE", "pending": "PENDING", "paused": "PAUSED"}
        label = status_label.get(d["status"], d["status"].upper())
        print(f"  {icon} {d['name']} ({count} decisions) ← {label}")

    # Active direction details
    active = get_active_direction(data)
    if active:
        print(f"\nCURRENT: {active['name']}")
        if active["decisions"]:
            last = active["decisions"][-1]
            print(f"LAST DECISION: {last}")
        else:
            print("LAST DECISION: (none yet)")
    else:
        print("\nNo active direction.")

    return 0


def cmd_recent(args: argparse.Namespace) -> int:
    """Show recent decisions from decisions.txt."""
    if not DECISIONS_FILE.exists():
        print("No decisions logged yet.")
        return 0

    lines = DECISIONS_FILE.read_text(encoding="utf-8").splitlines()
    n = args.n or 5

    # Get last n decision blocks
    decisions = []
    current = []
    for line in lines:
        if line.startswith("[") and "DECISION:" in line:
            if current:
                decisions.append("\n".join(current))
            current = [line]
        elif current:
            current.append(line)
    if current:
        decisions.append("\n".join(current))

    # Show last n
    recent = decisions[-n:]
    print(f"RECENT DECISIONS (last {len(recent)}):")
    print()
    for d in recent:
        print(d)
        print()

    return 0


def cmd_list(args: argparse.Namespace) -> int:
    """List all directions."""
    data = load_directions()

    if not data["directions"]:
        print("No directions set.")
        return 0

    print(f"GOAL: {data['goal']}")
    print()
    for d in data["directions"]:
        print(f"  {d['id']}: {d['name']} [{d['status']}]")

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Direction-aware decision trail for AI agents."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # init
    p_init = sub.add_parser("init", help="Initialize a new session")
    p_init.add_argument("goal", nargs="?", help="Goal description")

    # add
    p_add = sub.add_parser("add", help="Add a direction")
    p_add.add_argument("direction_id", help="Direction ID (kebab-case)")
    p_add.add_argument("name", help="Direction name")

    # start
    p_start = sub.add_parser("start", help="Start a direction")
    p_start.add_argument("direction_id", help="Direction ID")

    # done
    p_done = sub.add_parser("done", help="Mark direction as done")
    p_done.add_argument("direction_id", help="Direction ID")

    # log
    p_log = sub.add_parser("log", help="Log a decision")
    p_log.add_argument("direction_id", help="Direction ID")
    p_log.add_argument("action", help="What was done")
    p_log.add_argument("result", help="What happened / why")

    # status
    sub.add_parser("status", help="Show current status")

    # recent
    p_recent = sub.add_parser("recent", help="Show recent decisions")
    p_recent.add_argument("n", nargs="?", type=int, default=5, help="Number of decisions")

    # list
    sub.add_parser("list", help="List all directions")

    args = parser.parse_args()

    commands = {
        "init": cmd_init,
        "add": cmd_add,
        "start": cmd_start,
        "done": cmd_done,
        "log": cmd_log,
        "status": cmd_status,
        "recent": cmd_recent,
        "list": cmd_list,
    }

    return commands[args.command](args)


if __name__ == "__main__":
    sys.exit(main())

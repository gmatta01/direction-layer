# Direction Layer

A direction-aware decision trail for AI agents.

**One goal. Multiple directions. Track which path you're on.**

## Problem

AI agents keep forgetting:
- What decisions were made
- Which direction they're working on
- What's done vs pending

## Solution

Two simple files:

| File | What It Does |
|------|--------------|
| `directions.json` | Tracks which paths exist and their status |
| `decisions.txt` | Records what was chosen within each direction |

## Install

```bash
# Install the decision log dependency
pip install agent-decision-log

# Clone this repo
git clone https://github.com/YOUR_USERNAME/direction-layer.git
cd direction-layer

# Make executable
chmod +x directions.py
```

## Usage

```bash
# Initialize with a goal
./directions.py init "Refactor parser for speed"

# Add directions
./directions.py add "optimize-hot-loop" "Optimize hot loop"
./directions.py add "add-caching" "Add caching"
./directions.py add "reduce-alloc" "Reduce allocations"

# Start working on one
./directions.py start "optimize-hot-loop"

# Log decisions as you work
./directions.py log "optimize-hot-loop" "read parser.ts" "found hot loop at line 42"
./directions.py log "optimize-hot-loop" "check tests" "tests exist, safe to refactor"
./directions.py log "optimize-hot-loop" "edit parser" "switched to AST parsing"

# Check status
./directions.py status

# Mark done, move to next
./directions.py done "optimize-hot-loop"
./directions.py start "add-caching"

# Review recent decisions
./directions.py recent 5
```

## Status Icons

| Icon | Status | Meaning |
|------|--------|---------|
| `✓` | DONE | Direction completed |
| `→` | ACTIVE | Currently working on this |
| `⏳` | PENDING | Not started yet |
| `⏸` | PAUSED | Was active, now paused |

## Output Example

```
GOAL: Refactor parser for speed

DIRECTIONS:
  ✓ Optimize hot loop (3 decisions) ← DONE
  → Add caching (2 decisions) ← ACTIVE
  ⏳ Reduce allocations (0 decisions) ← PENDING

CURRENT: Add caching
LAST DECISION: 2026-09-18 10:05
```

## How It Works

1. **Goal** is set once at the beginning
2. **Directions** are multiple paths to achieve the goal
3. **Decisions** are logged within each direction
4. Agent queries `--status` to know where it is

## Files Created

- `directions.json` - Your directions and their status
- `decisions.txt` - Decision log (append-only)

## Pi Extension (Auto-Inject Status)

The `pi-extension/` directory contains a Pi extension that automatically injects direction status after every tool call.

### Install

```bash
cp pi-extension/direction-layer.ts ~/.pi/agent/extensions/
```

### What It Does

After every tool call, you'll see:
```
[direction-layer] → Optimize hot loop (3 decisions) | Last: 2026-09-11 10:30:00 | 1/3 done, 1 pending
```

The agent sees this automatically - no manual `--status` checks needed.

## License

MIT

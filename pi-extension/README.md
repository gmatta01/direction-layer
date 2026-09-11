# Direction Layer - Pi Extension

Injects direction status after every tool call.

## Install

The extension is already installed at:
```
~/.pi/agent/extensions/direction-layer.ts
```

## Usage

1. Initialize a direction session in your workspace:
```bash
python3 directions.py init "Your goal here"
python3 directions.py add "direction-1" "First direction"
python3 directions.py add "direction-2" "Second direction"
```

2. Use Pi normally. After every tool call, you'll see:
```
[direction-layer] → First direction (3 decisions) | Last: 2026-09-11 10:30:00 | 0/2 done, 1 pending
```

3. Update directions with the CLI:
```bash
python3 directions.py start "direction-1"
python3 directions.py log "direction-1" "action" "result"
python3 directions.py done "direction-1"
```

## What It Does

- Reads `directions.json` from workspace
- After every tool call, appends direction status to the result
- Shows: active direction, decision count, last decision, completion progress
- Agent sees this automatically - no manual checking needed

## Requirements

- `directions.json` in workspace (created by `directions.py init`)
- Node.js Pi extension system (auto-loaded from `~/.pi/agent/extensions/`)

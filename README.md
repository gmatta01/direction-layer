# Direction Layer

A Pi extension for direction-aware decision tracking.

**Slash command: `/direction`**

## What It Does

- Interactive onboarding (goal + directions)
- Session-persistent state
- Auto-injects status after every tool call
- Track decisions within each direction

## Install

```bash
cp pi-extension/direction-layer.ts ~/.pi/agent/extensions/
```

Then restart Pi or `/reload`.

## Usage

### Start a direction session

```
/direction
```

This starts an interactive onboarding:
1. Enter your goal
2. List your directions (comma-separated)
3. Confirm

### Commands

| Command | What it does |
|---------|--------------|
| `/direction` | Start onboarding |
| `/direction status` | Show current status |
| `/direction done` | Mark current direction as done, start next |
| `/direction log <action> <result>` | Log a decision |
| `/direction list` | List all directions |

### Auto-inject

After every tool call, you'll see:
```
[direction] → Optimize hot loop (3 decisions) | Last: read parser.ts | 1/3 done
```

## Example

```
/direction
> Goal: Refactor parser for speed
> Directions: optimize hot loop, add caching, reduce allocations

[Direction layer initialized]

# Work normally - status auto-injects after every tool call

/direction done
> Completed: optimize hot loop (3 decisions)
> Next: add caching

/direction list
> GOAL: Refactor parser for speed
> ✓ optimize hot loop (3 decisions)
> → add caching (0 decisions)
> ⏳ reduce allocations (0 decisions)
```

## License

MIT

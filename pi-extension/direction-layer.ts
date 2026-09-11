/**
 * direction-layer.ts - Pi extension for direction-aware decision tracking
 * 
 * Slash command: /direction
 * - Interactive onboarding (goal + directions)
 * - Session-persistent state
 * - Auto-injects status after every tool call
 */

import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";

interface Direction {
  id: string;
  name: string;
  status: "active" | "done" | "pending" | "paused";
  decisions: { timestamp: string; action: string; result: string }[];
}

interface DirectionState {
  goal: string;
  directions: Direction[];
  started: string;
}

function getActiveDirection(state: DirectionState): Direction | undefined {
  return state.directions.find(d => d.status === "active");
}

function formatStatus(state: DirectionState): string {
  const active = getActiveDirection(state);
  const done = state.directions.filter(d => d.status === "done").length;
  const total = state.directions.length;
  
  if (!active) {
    return `[direction] No active direction | ${done}/${total} done`;
  }
  
  const lastDecision = active.decisions.length > 0 
    ? active.decisions[active.decisions.length - 1].action
    : "none yet";
  
  return `[direction] → ${active.name} (${active.decisions.length} decisions) | Last: ${lastDecision} | ${done}/${total} done`;
}

export default function (pi: ExtensionAPI) {
  let state: DirectionState | null = null;

  // Slash command: /direction
  pi.registerCommand("direction", {
    description: "Initialize or manage direction layer for this session",
    handler: async (args, ctx) => {
      const subcommand = args?.trim().split(" ")[0] || "";

      // /direction - start onboarding
      if (!subcommand || subcommand === "start") {
        if (state) {
          ctx.ui.notify("Direction layer already active. Use /direction status", "warning");
          return;
        }

        // Ask for goal
        const goal = await ctx.ui.input({
          title: "What is the goal for this session?",
          placeholder: "e.g., Refactor parser for speed"
        });
        if (!goal) {
          ctx.ui.notify("Goal required. Aborted.", "error");
          return;
        }

        // Ask for directions
        const directionsText = await ctx.ui.input({
          title: "List your directions (one per line, or comma-separated)",
          placeholder: "e.g., optimize hot loop, add caching, reduce allocations"
        });
        if (!directionsText) {
          ctx.ui.notify("Directions required. Aborted.", "error");
          return;
        }

        // Parse directions
        const dirNames = directionsText
          .split(/[,\n]/)
          .map(d => d.trim())
          .filter(d => d.length > 0);

        const directions: Direction[] = dirNames.map((name, i) => ({
          id: name.toLowerCase().replace(/[^a-z0-9]+/g, "-"),
          name,
          status: i === 0 ? "active" : "pending",
          decisions: []
        }));

        // Confirm
        const summary = `GOAL: ${goal}\n\nDIRECTIONS:\n${directions.map((d, i) => 
          `${d.status === "active" ? "→" : "⏳"} ${d.name}`
        ).join("\n")}`;

        const confirmed = await ctx.ui.confirm({
          title: "Confirm directions?",
          description: summary
        });

        if (!confirmed) {
          ctx.ui.notify("Aborted.", "info");
          return;
        }

        // Save state
        state = {
          goal,
          directions,
          started: new Date().toISOString()
        };

        // Persist to session
        pi.appendEntry({
          customType: "direction-layer",
          content: JSON.stringify(state),
          display: false
        });

        ctx.ui.notify(`Direction layer initialized: ${goal}`, "success");
        return;
      }

      // /direction status
      if (subcommand === "status" || subcommand === "s") {
        if (!state) {
          ctx.ui.notify("No direction layer. Use /direction to start.", "warning");
          return;
        }
        ctx.ui.notify(formatStatus(state), "info");
        return;
      }

      // /direction done [name]
      if (subcommand === "done" || subcommand === "d") {
        if (!state) {
          ctx.ui.notify("No direction layer active.", "warning");
          return;
        }

        const active = getActiveDirection(state);
        if (!active) {
          ctx.ui.notify("No active direction to complete.", "warning");
          return;
        }

        active.status = "done";
        ctx.ui.notify(`Completed: ${active.name} (${active.decisions.length} decisions)`, "success");

        // Start next pending
        const next = state.directions.find(d => d.status === "pending");
        if (next) {
          next.status = "active";
          ctx.ui.notify(`Next: ${next.name}`, "info");
        } else {
          ctx.ui.notify("All directions complete! 🎉", "success");
        }

        // Persist
        pi.appendEntry({
          customType: "direction-layer",
          content: JSON.stringify(state),
          display: false
        });
        return;
      }

      // /direction log <action> <result>
      if (subcommand === "log" || subcommand === "l") {
        if (!state) {
          ctx.ui.notify("No direction layer active.", "warning");
          return;
        }

        const active = getActiveDirection(state);
        if (!active) {
          ctx.ui.notify("No active direction.", "warning");
          return;
        }

        const parts = args?.trim().split(" ").slice(1) || [];
        const action = parts[0] || await ctx.ui.input({ title: "Action taken:" });
        const result = parts.slice(1).join(" ") || await ctx.ui.input({ title: "Result/why:" });

        if (action) {
          active.decisions.push({
            timestamp: new Date().toISOString(),
            action,
            result: result || ""
          });

          pi.appendEntry({
            customType: "direction-layer",
            content: JSON.stringify(state),
            display: false
          });

          ctx.ui.notify(`Logged: ${action}`, "success");
        }
        return;
      }

      // /direction list
      if (subcommand === "list" || subcommand === "ls") {
        if (!state) {
          ctx.ui.notify("No direction layer active.", "warning");
          return;
        }

        const lines = state.directions.map(d => {
          const icon = d.status === "done" ? "✓" : d.status === "active" ? "→" : "⏳";
          return `${icon} ${d.name} (${d.decisions.length} decisions)`;
        });

        ctx.ui.notify(`GOAL: ${state.goal}\n\n${lines.join("\n")}`, "info");
        return;
      }

      // Unknown subcommand
      ctx.ui.notify("Usage: /direction [start|status|done|log|list]", "info");
    }
  });

  // Auto-inject status after every tool call
  pi.on("tool_result", async (event, ctx) => {
    if (!state) return;

    const statusLine = formatStatus(state);
    
    const currentContent = event.content || [];
    const newContent = [
      ...currentContent,
      { type: "text" as const, text: `\n${statusLine}` }
    ];

    return { content: newContent };
  });

  // Restore state from session on load
  pi.on("session_start", async (event, ctx) => {
    // Check for existing direction-layer entries
    const entries = ctx.sessionManager.getEntries?.("direction-layer") || [];
    if (entries.length > 0) {
      const last = entries[entries.length - 1];
      try {
        state = JSON.parse(last.content);
      } catch {
        // Ignore parse errors
      }
    }
  });
}

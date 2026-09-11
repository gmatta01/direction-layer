/**
 * direction-layer.ts - Pi extension for direction-aware decision tracking
 * 
 * Injects direction status after every tool call.
 * Reads directions.json from workspace, shows active direction + decision count.
 * 
 * Install: Place in ~/.pi/agent/extensions/
 * Requires: directions.json in workspace (created by directions.py init)
 */

import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { readFileSync, existsSync } from "fs";
import { join } from "path";

interface Direction {
  id: string;
  name: string;
  status: "active" | "done" | "pending" | "paused";
  decisions: string[];
}

interface DirectionsData {
  goal: string;
  created: string;
  directions: Direction[];
}

function loadDirections(cwd: string): DirectionsData | null {
  const filePath = join(cwd, "directions.json");
  if (!existsSync(filePath)) return null;
  
  try {
    const content = readFileSync(filePath, "utf-8");
    return JSON.parse(content);
  } catch {
    return null;
  }
}

function formatStatus(data: DirectionsData): string {
  const active = data.directions.find(d => d.status === "active");
  const done = data.directions.filter(d => d.status === "done").length;
  const pending = data.directions.filter(d => d.status === "pending").length;
  const total = data.directions.length;
  
  const parts: string[] = [];
  
  if (active) {
    const lastDecision = active.decisions.length > 0 
      ? active.decisions[active.decisions.length - 1]
      : "none";
    parts.push(`→ ${active.name} (${active.decisions.length} decisions)`);
    parts.push(`Last: ${lastDecision}`);
  }
  
  parts.push(`${done}/${total} done, ${pending} pending`);
  
  return `[direction-layer] ${parts.join(" | ")}`;
}

export default function (pi: ExtensionAPI) {
  pi.on("tool_result", async (event, ctx) => {
    // Get working directory from context
    const cwd = ctx.cwd || process.cwd();
    
    // Load directions
    const data = loadDirections(cwd);
    if (!data || data.directions.length === 0) {
      return; // No directions file or no directions - skip
    }
    
    // Format status line
    const statusLine = formatStatus(data);
    
    // Append to tool result content
    const currentContent = event.content || [];
    const newContent = [
      ...currentContent,
      { type: "text" as const, text: `\n${statusLine}` }
    ];
    
    return { content: newContent };
  });
}

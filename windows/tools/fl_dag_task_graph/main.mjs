#!/usr/bin/env node
/**
 * 🎯 fl_dag_task_graph - DAG Tracer-Bullet Task Graph & Frontier Engine
 * Validates acyclicity, computes topological sort, and calculates the active execution frontier.
 * Co-authored-by: Flowork OS <agent@floworkos.com>
 */
process.on("uncaughtException", (err) => {
  console.log(JSON.stringify({ status: "error", error: "UNCAUGHT_EXCEPTION", message: err.message }, null, 2));
  process.exit(0);
});
process.on("unhandledRejection", (reason) => {
  console.log(JSON.stringify({ status: "error", error: "UNHANDLED_REJECTION", message: String(reason) }, null, 2));
  process.exit(0);
});

import fs from 'fs';
import path from 'path';

function parseArgs() {
  const args = process.argv.slice(2);
  let params = {};
  const pIdx = args.indexOf('--params');
  if (pIdx !== -1 && args[pIdx + 1]) {
    try { params = JSON.parse(args[pIdx + 1]); } catch (_) {}
  } else if (args[0] && args[0].startsWith('{')) {
    try { params = JSON.parse(args[0]); } catch (_) {}
  }
  return params;
}

function parseTasksInput(params) {
  let tasks = [];
  if (params.tasks_json) {
    try {
      const parsed = typeof params.tasks_json === 'string' ? JSON.parse(params.tasks_json) : params.tasks_json;
      tasks = Array.isArray(parsed) ? parsed : parsed.tasks || [];
    } catch (_) {}
  } else if (params.tasks_file) {
    const filePath = path.resolve(params.tasks_file);
    if (fs.existsSync(filePath)) {
      const raw = fs.readFileSync(filePath, 'utf8');
      try {
        const parsed = JSON.parse(raw);
        tasks = Array.isArray(parsed) ? parsed : parsed.tasks || [];
      } catch (_) {
        // Markdown checklist parser fallback
        const lines = raw.split('\n');
        for (const line of lines) {
          const match = line.match(/^[-*]\s*\[([ xX])\]\s*([A-Za-z0-9_-]+)\s*:\s*(.*?)(?:\s*\((?:blocked_by|depends_on):\s*([^)]+)\))?$/);
          if (match) {
            const blockedBy = match[4] ? match[4].split(',').map(s => s.trim()).filter(Boolean) : [];
            tasks.push({
              id: match[2].trim(),
              title: match[3].trim(),
              status: match[1].toLowerCase() === 'x' ? 'done' : 'pending',
              blocked_by: blockedBy
            });
          }
        }
      }
    }
  }

  // Normalize
  return tasks.map(t => ({
    id: String(t.id || t.ticket_id || '').trim(),
    title: String(t.title || t.name || '').trim(),
    status: (t.status || 'pending').toLowerCase(),
    blocked_by: Array.isArray(t.blocked_by)
      ? t.blocked_by.map(String)
      : Array.isArray(t.depends_on)
      ? t.depends_on.map(String)
      : typeof t.blocked_by === 'string'
      ? t.blocked_by.split(',').map(s => s.trim()).filter(Boolean)
      : []
  })).filter(t => t.id);
}

function detectCycles(tasks) {
  const adj = new Map();
  for (const t of tasks) {
    adj.set(t.id, t.blocked_by || []);
  }

  const visited = new Map(); // 0: unvisited, 1: visiting, 2: visited
  const cyclePath = [];

  function dfs(node, pathStack) {
    visited.set(node, 1);
    pathStack.push(node);

    const neighbors = adj.get(node) || [];
    for (const neighbor of neighbors) {
      if (!adj.has(neighbor)) continue; // external/resolved reference
      const state = visited.get(neighbor) || 0;
      if (state === 1) {
        cyclePath.push([...pathStack, neighbor]);
        return true;
      }
      if (state === 0 && dfs(neighbor, pathStack)) {
        return true;
      }
    }

    pathStack.pop();
    visited.set(node, 2);
    return false;
  }

  for (const t of tasks) {
    if ((visited.get(t.id) || 0) === 0) {
      if (dfs(t.id, [])) {
        return cyclePath[0];
      }
    }
  }
  return null;
}

function computeTopologicalSort(tasks) {
  const inDegree = new Map();
  const graph = new Map(); // dependency -> dependents

  for (const t of tasks) {
    inDegree.set(t.id, 0);
    graph.set(t.id, []);
  }

  for (const t of tasks) {
    for (const dep of t.blocked_by) {
      if (graph.has(dep)) {
        graph.get(dep).push(t.id);
        inDegree.set(t.id, (inDegree.get(t.id) || 0) + 1);
      }
    }
  }

  const queue = [];
  for (const [id, deg] of inDegree.entries()) {
    if (deg === 0) queue.push(id);
  }

  const sorted = [];
  while (queue.length > 0) {
    const curr = queue.shift();
    sorted.push(curr);
    for (const nxt of graph.get(curr) || []) {
      inDegree.set(nxt, inDegree.get(nxt) - 1);
      if (inDegree.get(nxt) === 0) {
        queue.push(nxt);
      }
    }
  }

  return sorted;
}

function generateMermaidDiagram(tasks, frontierIds, doneIds) {
  let mermaid = "graph TD\n";
  for (const t of tasks) {
    const isDone = doneIds.has(t.id);
    const isFrontier = frontierIds.has(t.id);
    const label = `${t.id}["${t.title}"]`;

    if (isDone) {
      mermaid += `  ${t.id}${label}:::doneNode\n`;
    } else if (isFrontier) {
      mermaid += `  ${t.id}${label}:::frontierNode\n`;
    } else {
      mermaid += `  ${t.id}${label}:::blockedNode\n`;
    }

    for (const dep of t.blocked_by) {
      mermaid += `  ${dep} --> ${t.id}\n`;
    }
  }

  mermaid += "  classDef doneNode fill:#1f6feb,stroke:#388bfd,stroke-width:2px,color:#fff;\n";
  mermaid += "  classDef frontierNode fill:#238636,stroke:#2ea043,stroke-width:3px,color:#fff;\n";
  mermaid += "  classDef blockedNode fill:#21262d,stroke:#30363d,stroke-width:1px,color:#8b949e;\n";
  return mermaid;
}

function main() {
  const params = parseArgs();
  const action = params.action || 'evaluate_frontier';
  const tasks = parseTasksInput(params);

  if (tasks.length === 0) {
    console.log(JSON.stringify({
      status: "error",
      message: "No valid tasks provided. Provide tasks_json or tasks_file containing an array of task objects."
    }, null, 2));
    return;
  }

  // 1. Cycle validation
  const cycle = detectCycles(tasks);
  if (cycle) {
    console.log(JSON.stringify({
      status: "error",
      error: "CYCLIC_DEPENDENCY_DETECTED",
      message: `Invalid DAG: Detected circular dependency chain: ${cycle.join(' -> ')}`,
      cycle_path: cycle
    }, null, 2));
    return;
  }

  // 2. Resolve set
  const doneSet = new Set();
  for (const t of tasks) {
    if (t.status === 'done' || t.status === 'completed') {
      doneSet.add(t.id);
    }
  }
  if (params.resolved_task_ids) {
    params.resolved_task_ids.split(',').map(s => s.trim()).filter(Boolean).forEach(id => doneSet.add(id));
  }

  // 3. Compute Active Frontier
  const frontier = [];
  const blocked = [];

  for (const t of tasks) {
    if (doneSet.has(t.id)) continue;
    const remainingBlockers = t.blocked_by.filter(dep => !doneSet.has(dep));
    if (remainingBlockers.length === 0) {
      frontier.push(t);
    } else {
      blocked.push({
        ...t,
        waiting_on: remainingBlockers
      });
    }
  }

  const frontierSet = new Set(frontier.map(t => t.id));
  const topoOrder = computeTopologicalSort(tasks);
  const mermaidDiagram = generateMermaidDiagram(tasks, frontierSet, doneSet);

  if (action === 'validate_dag') {
    console.log(JSON.stringify({
      status: "success",
      is_valid_dag: true,
      total_nodes: tasks.length,
      topological_order: topoOrder
    }, null, 2));
    return;
  }

  if (action === 'generate_mermaid') {
    console.log(JSON.stringify({
      status: "success",
      mermaid: mermaidDiagram
    }, null, 2));
    return;
  }

  // Default: evaluate_frontier
  console.log(JSON.stringify({
    status: "success",
    action: "evaluate_frontier",
    total_tasks: tasks.length,
    completed_count: doneSet.size,
    frontier_ready_count: frontier.length,
    blocked_count: blocked.length,
    active_frontier: frontier.map(t => ({ id: t.id, title: t.title, ready_for: "parallel_worktree_dispatch" })),
    blocked_tasks: blocked.map(t => ({ id: t.id, title: t.title, waiting_on: t.waiting_on })),
    topological_sequence: topoOrder,
    mermaid: mermaidDiagram
  }, null, 2));
}

main();

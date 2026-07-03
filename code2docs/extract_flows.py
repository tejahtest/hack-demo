#!/usr/bin/env python3
"""extract_flows.py — turn the code graph into candidate "stories" (flows).

The hard, novel step of the pipeline (build step 2 in the plan). It is
DETERMINISTIC: no API key needed, so the pipeline always produces a valid
flows.json. It:

  1. Finds entry points   — function nodes that nobody else calls (roots of a
                            call tree) plus exported-interface name patterns.
                            Each seeds a candidate flow.
  2. Walks the call edges  — bounded, deduped DFS pre-order from each entry
                            point to build an ordered path.
  3. Narrates each path    — actors are the graph communities the path crosses
                            (rendered as sequence-diagram lanes); every step
                            gets a plain-language `say` and a technical `tech`.

The plain-language `say`/`title` text is templated here so the pipeline never
breaks; the "one LLM pass" in the plan then refines that prose into genuinely
readable stories (and the drift-aware agent re-narrates on merge).

Usage:
    python code2docs/extract_flows.py                 # write code2docs/flows.json
    python code2docs/extract_flows.py --dry-run       # print summary only
    python code2docs/extract_flows.py --out out.json  # custom output
"""

from __future__ import annotations

import argparse
import collections
import json
import re
from pathlib import Path

import c2d_common as c2d


def build_adjacency(graph: dict, relations: list[str]):
    """source_id -> list of (target_id, edge) for the walk relations."""
    adj = collections.defaultdict(list)
    calls_indeg = collections.Counter()
    calls_outdeg = collections.Counter()
    for e in graph["_edges"]:
        rel = e.get("relation")
        if rel in relations:
            adj[e["source"]].append((e["target"], e))
            calls_indeg[e["target"]] += 1
            calls_outdeg[e["source"]] += 1
    return adj, calls_indeg, calls_outdeg


def reachable_size(adj, start, nodes_by_id, limit=80) -> int:
    """Number of distinct function nodes reachable from start (bounded)."""
    seen = {start}
    queue = collections.deque([start])
    count = 0
    while queue and len(seen) < limit:
        cur = queue.popleft()
        for tgt, _ in adj.get(cur, []):
            if tgt in seen:
                continue
            seen.add(tgt)
            node = nodes_by_id.get(tgt)
            if node and c2d.is_function(node):
                count += 1
            queue.append(tgt)
    return count


def find_entry_points(graph, adj, indeg, outdeg, patterns):
    """Root function nodes, scored by reachable subtree size + name pattern."""
    nodes_by_id = graph["_nodes_by_id"]
    pat = [re.compile(p) for p in patterns]
    entries = []
    for nid, node in nodes_by_id.items():
        if not c2d.is_function(node):
            continue
        if outdeg[nid] < 1 or indeg[nid] != 0:
            continue  # not a root of the call tree
        label = node["label"]
        size = reachable_size(adj, nid, nodes_by_id)
        pattern_boost = 100 if any(p.search(label) for p in pat) else 0
        entries.append((pattern_boost + size, size, nid, node))
    # highest score first; ties broken by label for determinism
    entries.sort(key=lambda t: (-t[0], -t[1], nodes_by_id[t[2]]["label"]))
    return entries


def walk(adj, entry_id, nodes_by_id, max_depth, max_steps):
    """Bounded DFS pre-order. Returns ordered [(caller_id, callee_id, edge)]."""
    transitions = []
    visited = {entry_id}

    def dfs(node_id, depth):
        if depth >= max_depth or len(transitions) >= max_steps:
            return
        # deterministic order: by target label
        children = sorted(
            adj.get(node_id, []),
            key=lambda te: nodes_by_id.get(te[0], {}).get("label", ""),
        )
        for tgt, edge in children:
            if len(transitions) >= max_steps:
                return
            node = nodes_by_id.get(tgt)
            if node is None or not c2d.is_function(node):
                continue
            if tgt in visited:
                continue
            visited.add(tgt)
            transitions.append((node_id, tgt, edge))
            dfs(tgt, depth + 1)

    dfs(entry_id, 0)
    return transitions


def community_label(graph, labels, cid) -> str:
    return labels.get(str(cid), labels.get(cid, f"Component {cid}"))


def apply_override(flow: dict, ov: dict) -> None:
    """Merge editorial overrides (title/description/say-by-cap) into a flow."""
    if not ov:
        return
    if ov.get("title"):
        flow["title"] = ov["title"]
    if ov.get("description"):
        flow["description"] = ov["description"]
    say_by_cap = ov.get("say", {})
    for step in flow.get("steps", []):
        if step.get("cap") in say_by_cap:
            step["say"] = say_by_cap[step["cap"]]


def make_flow(graph, labels, entry_node, transitions, module_name):
    nodes_by_id = graph["_nodes_by_id"]

    # Lanes: user first, then each community the path crosses (first-seen order).
    lane_order = []                 # ordered list of community ids
    lane_index = {}                 # community id -> lane index (>=1)

    def lane_of(node):
        cid = node.get("community")
        if cid not in lane_index:
            lane_index[cid] = len(lane_order) + 1  # +1: user occupies lane 0
            lane_order.append(cid)
        return lane_index[cid]

    entry_lane = lane_of(entry_node)
    title = c2d.gerund_title(entry_node["label"])

    steps = []
    # Step 0: the user triggers the entry point.
    steps.append({
        "from": 0,
        "to": entry_lane,
        "cap": c2d.short_label(entry_node["label"]),
        "say": f'You start "{title}".',
        "tech": f"Entry point `{entry_node['label']}`  ·  "
                f"{entry_node.get('source_file','?')}:{entry_node.get('source_location','?')}",
        "fromId": "__user__",
        "toId": entry_node["id"],
        "rel": "triggers",
    })

    for caller_id, callee_id, edge in transitions:
        caller = nodes_by_id[caller_id]
        callee = nodes_by_id[callee_id]
        from_lane = lane_of(caller)
        to_lane = lane_of(callee)
        to_name = community_label(graph, labels, callee.get("community"))
        action = c2d.action_phrase(callee["label"])
        if from_lane == to_lane:
            say = action
        else:
            say = f"{to_name}: {action[0].lower()}{action[1:]}"
        steps.append({
            "from": from_lane,
            "to": to_lane,
            "cap": c2d.short_label(callee["label"]),
            "say": say,
            "tech": f"`{caller['label']}` -> `{callee['label']}`  ·  "
                    f"{callee.get('source_file','?')}:{edge.get('source_location','?')}",
            "fromId": caller_id,
            "toId": callee_id,
            "rel": edge.get("relation", "calls"),
        })

    actors = [{"name": "You", "emoji": "\U0001f9d1"}]
    for cid in lane_order:
        name = community_label(graph, labels, cid)
        actors.append({"name": name, "emoji": c2d.emoji_for(name), "community": cid})

    return {
        "id": c2d.slugify(c2d.readable(entry_node["label"])),
        "title": title,
        "module": module_name,
        "entry": {
            "id": entry_node["id"],
            "label": entry_node["label"],
            "file": entry_node.get("source_file"),
        },
        "actors": actors,
        "steps": steps,
    }


def main():
    ap = argparse.ArgumentParser(description="Extract candidate flows from the code graph.")
    ap.add_argument("--config", default=None)
    ap.add_argument("--graph", default=None, help="override graph.json path")
    ap.add_argument("--out", default=None, help="override flows.json output path")
    ap.add_argument("--dry-run", action="store_true", help="print summary, don't write")
    args = ap.parse_args()

    c2d.init_io()
    cfg = c2d.load_config(args.config)
    graph = c2d.load_graph(cfg, args.graph)
    ex = cfg.get("extract", {})
    relations = ex.get("walk_relations", ["calls"])
    # Lane names: derive from the dominant source folder of each community
    # (deterministic, no API key); let a real graphify label file override.
    labels = c2d.derive_community_labels(graph)
    labels_path = c2d.REPO_ROOT / "graphify-out" / ".graphify_labels.json"
    if labels_path.exists():
        labels.update(json.loads(labels_path.read_text(encoding="utf-8")))

    version = c2d.read_version(cfg)
    adj, indeg, outdeg = build_adjacency(graph, relations)
    entries = find_entry_points(graph, adj, indeg, outdeg,
                                ex.get("entry_point_patterns", []))

    # Editorial curation layer (the "one LLM pass"): a data file of per-flow
    # title/description/say overrides, merged in without losing reproducibility.
    ov_path = c2d.REPO_ROOT / "code2docs" / "flow_overrides.json"
    overrides = json.loads(ov_path.read_text(encoding="utf-8")) if ov_path.exists() else {}

    flows = []
    used_ids = set()
    for score, size, entry_id, entry_node in entries:
        if len(flows) >= ex.get("max_flows", 8):
            break
        transitions = walk(adj, entry_id, graph["_nodes_by_id"],
                           ex.get("max_depth", 4), ex.get("max_steps", 8))
        if len(transitions) < ex.get("min_steps", 2):
            continue
        flow = make_flow(graph, labels, entry_node, transitions, cfg["module_name"])
        if flow["id"] in used_ids:
            continue
        apply_override(flow, overrides.get(flow["id"], {}))
        used_ids.add(flow["id"])
        flows.append(flow)

    doc = {
        "module": cfg["module_name"],
        "moduleRoot": cfg["module_root"],
        "version": version,
        "baselineVersion": c2d.short_version(version),
        "generatedFrom": graph.get("built_at_commit"),
        "flows": flows,
    }

    print(f"Extracted {len(flows)} flows from {len(entries)} entry candidates "
          f"(module {cfg['module_name']} v{version}):")
    for f in flows:
        print(f"  - {f['id']:32s} {len(f['steps'])} steps, "
              f"{len(f['actors'])} lanes  [{f['entry']['label']}]")

    if args.dry_run:
        return

    out_path = Path(args.out) if args.out else c2d._abs(cfg["flows_path"])
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(doc, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nWrote {out_path}")


if __name__ == "__main__":
    main()

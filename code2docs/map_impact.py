#!/usr/bin/env python3
"""map_impact.py — changed files -> impacted flows + edge deltas (deterministic).

The first of the two pieces that make the post-merge update work. Given the
list of files a merge changed:

  1. Map each changed file to its graph nodes, then to the flows those nodes
     appear in  -> the impacted flow IDs.
  2. Diff the edge set of the new graph against a base graph -> addedEdges /
     removedEdges (each is source -> target with a relation).
  3. Turn those deltas into a per-flow highlight plan: an added edge landing on
     an impacted flow's path becomes a NEW step tagged with the new version; a
     removed/changed edge marks an existing step as CHANGED.

Output: impacted.json. With --apply-flows the highlight plan is written back
into flows.json so the living docs and Mermaid diagrams render the change
automatically (the drift-aware agent then refines the narration).

Usage:
    python code2docs/map_impact.py changed.txt
    python code2docs/map_impact.py changed.txt --base-graph base-graph.json
    python code2docs/map_impact.py changed.txt --base-graph base.json --apply-flows
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import c2d_common as c2d


def norm(p: str) -> str:
    return p.replace("\\", "/").strip().lstrip("./")


def to_module_relative(repo_path: str, module_root: str) -> str | None:
    """Repo-relative path -> module-relative source_file, or None if outside."""
    rp, mr = norm(repo_path), norm(module_root)
    if rp == mr:
        return ""
    if rp.startswith(mr + "/"):
        return rp[len(mr) + 1:]
    return None


def edge_set(graph: dict) -> set[tuple]:
    return {(e["source"], e["target"], e.get("relation", "")) for e in graph["_edges"]}


def edge_lookup(graph: dict) -> dict:
    """(source, target, relation) -> edge dict, for recovering source_location."""
    return {(e["source"], e["target"], e.get("relation", "")): e for e in graph["_edges"]}


def flow_node_ids(flow: dict) -> set[str]:
    ids = {flow.get("entry", {}).get("id")}
    for s in flow.get("steps", []):
        ids.add(s.get("fromId"))
        ids.add(s.get("toId"))
    ids.discard("__user__")
    ids.discard(None)
    return ids


def main():
    ap = argparse.ArgumentParser(description="Map changed files to impacted flows + edge deltas.")
    ap.add_argument("changed", help="text file: one changed repo-relative path per line")
    ap.add_argument("--config", default=None)
    ap.add_argument("--graph", default=None, help="override (new) graph.json path")
    ap.add_argument("--base-graph", default=None, help="previous graph.json for edge diff")
    ap.add_argument("--flows", default=None, help="override flows.json path")
    ap.add_argument("--out", default=None, help="impacted.json output path (default code2docs/impacted.json)")
    ap.add_argument("--apply-flows", action="store_true",
                    help="write the highlight plan back into flows.json")
    args = ap.parse_args()

    c2d.init_io()
    cfg = c2d.load_config(args.config)
    module_root = cfg["module_root"]
    graph = c2d.load_graph(cfg, args.graph)
    new_nodes = graph["_nodes_by_id"]
    version = c2d.short_version(c2d.read_version(cfg))

    flows_path = Path(args.flows) if args.flows else c2d._abs(cfg["flows_path"])
    doc = json.loads(flows_path.read_text(encoding="utf-8"))
    flows = doc.get("flows", [])

    # --- 1. changed files -> module-relative + impacted nodes / communities ---
    raw = [l for l in Path(args.changed).read_text(encoding="utf-8").splitlines() if l.strip()]
    module_files = set()
    for rp in raw:
        mrel = to_module_relative(rp, module_root)
        if mrel is not None and mrel != "":
            module_files.add(mrel)

    impacted_nodes = set()
    impacted_comms = set()
    for n in graph.get("nodes", []):
        if n.get("source_file") in module_files:
            impacted_nodes.add(n["id"])
            if n.get("community") is not None:
                impacted_comms.add(n["community"])

    # --- 2. edge deltas vs base graph -------------------------------------
    added_edges, removed_edges = [], []
    if args.base_graph and Path(args.base_graph).exists():
        base = c2d.load_graph(cfg, args.base_graph)
        new_set, base_set = edge_set(graph), edge_set(base)
        new_look, base_look = edge_lookup(graph), edge_lookup(base)

        def as_edge(key, look):
            s, t, r = key
            loc = look.get(key, {}).get("source_location", "")
            return {"source": s, "target": t, "relation": r, "source_location": loc}

        added_edges = [as_edge(k, new_look) for k in sorted(new_set - base_set)]
        removed_edges = [as_edge(k, base_look) for k in sorted(base_set - new_set)]

    # --- 3. impacted flows + per-flow highlight plan ----------------------
    impacted = []
    for flow in flows:
        fids = flow_node_ids(flow)
        reasons = []
        # a node the flow uses lives in a changed file
        if fids & impacted_nodes:
            reasons.append("changed-file")
        # a node the flow uses was deleted from the graph
        if any(fid not in new_nodes for fid in fids):
            reasons.append("removed-node")
        # a component (community) the flow crosses changed
        flow_comms = {a.get("community") for a in flow.get("actors", []) if a.get("community") is not None}
        if flow_comms & impacted_comms:
            reasons.append("changed-component")

        changes = plan_changes(flow, fids, added_edges, removed_edges, new_nodes, version)
        if reasons or changes["addSteps"] or changes["markChanged"]:
            impacted.append({"id": flow["id"], "reasons": sorted(set(reasons)), "changes": changes})

    result = {
        "module": cfg["module_name"],
        "version": version,
        "changedFiles": [norm(p) for p in raw],
        "moduleChangedFiles": sorted(module_files),
        "impactedNodes": sorted(impacted_nodes),
        "impactedCommunities": sorted(impacted_comms),
        "addedEdges": added_edges,
        "removedEdges": removed_edges,
        "flows": [f["id"] for f in impacted],
        "flowDetails": impacted,
    }

    out_path = Path(args.out) if args.out else c2d.REPO_ROOT / "code2docs" / "impacted.json"
    out_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"Impacted: {len(impacted)} / {len(flows)} flows  "
          f"({len(module_files)} module files changed, "
          f"+{len(added_edges)} / -{len(removed_edges)} edges)")
    for f in impacted:
        print(f"  - {f['id']:30s} {','.join(f['reasons']) or 'edge-delta'}"
              f"  (+{len(f['changes']['addSteps'])} steps, "
              f"{len(f['changes']['markChanged'])} changed)")
    print(f"Wrote {out_path}")

    if args.apply_flows:
        n = apply_highlights(doc, impacted, new_nodes, version)
        flows_path.write_text(json.dumps(doc, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Applied highlights to {n} flow(s) -> {flows_path}")


def plan_changes(flow, fids, added_edges, removed_edges, new_nodes, version):
    """Deterministic diff->highlight plan for one flow.

    addSteps:  added edge whose source is already on this flow's path but whose
               target is not -> a new step to insert after the source's step.
    markChanged: added/removed edge that lies between two nodes already adjacent
               on the path -> that step is flagged changed.
    """
    on_path = fids
    step_by_pair = {}
    for i, s in enumerate(flow.get("steps", [])):
        step_by_pair[(s.get("fromId"), s.get("toId"))] = i

    add_steps, mark_changed = [], []
    for e in added_edges:
        s, t = e["source"], e["target"]
        pair = (s, t)
        if pair in step_by_pair:
            mark_changed.append({"step": step_by_pair[pair], "edge": e})
        elif s in on_path and t not in on_path and t in new_nodes:
            add_steps.append({"afterNode": s, "edge": e})
    for e in removed_edges:
        pair = (e["source"], e["target"])
        if pair in step_by_pair:
            mark_changed.append({"step": step_by_pair[pair], "edge": e, "removed": True})
    return {"addSteps": add_steps, "markChanged": mark_changed}


def apply_highlights(doc, impacted, new_nodes, version):
    """Write since/changed markers and new steps into flows.json in place."""
    by_id = {f["id"]: f for f in doc.get("flows", [])}
    touched = 0
    for det in impacted:
        flow = by_id.get(det["id"])
        if not flow:
            continue
        changes = det["changes"]
        # mark changed steps
        for mc in changes["markChanged"]:
            idx = mc["step"]
            if 0 <= idx < len(flow["steps"]):
                flow["steps"][idx]["changed"] = True
        # community -> lane index, extending actors if a new lane is needed
        lane_of = {a.get("community"): i for i, a in enumerate(flow["actors"]) if a.get("community") is not None}

        def lane_for(cid, name):
            if cid in lane_of:
                return lane_of[cid]
            flow["actors"].append({"name": name, "emoji": c2d.emoji_for(name), "community": cid})
            lane_of[cid] = len(flow["actors"]) - 1
            return lane_of[cid]

        for add in changes["addSteps"]:
            src_id, e = add["afterNode"], add["edge"]
            tgt = new_nodes.get(e["target"])
            src = new_nodes.get(src_id)
            if not tgt or not src:
                continue
            from_lane = lane_for(src.get("community"), f"Component {src.get('community')}")
            to_lane = lane_for(tgt.get("community"), f"Component {tgt.get('community')}")
            action = c2d.action_phrase(tgt["label"])
            new_step = {
                "from": from_lane, "to": to_lane,
                "cap": tgt["label"].rstrip("()") or tgt["label"],
                "say": action, "since": version, "changed": False,
                "tech": f"`{src['label']}` -> `{tgt['label']}`  ·  "
                        f"{tgt.get('source_file','?')}:{e.get('source_location','?')}",
                "fromId": src_id, "toId": e["target"], "rel": e.get("relation", "calls"),
            }
            # insert right after the last step that ends at src, else append
            insert_at = len(flow["steps"])
            for i, s in enumerate(flow["steps"]):
                if s.get("toId") == src_id:
                    insert_at = i + 1
            flow["steps"].insert(insert_at, new_step)
        if changes["addSteps"] or changes["markChanged"]:
            flow["release"] = {"version": version}
            touched += 1
    return touched


if __name__ == "__main__":
    main()

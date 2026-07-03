# Code2Docs

Release-aware documentation hub and update agent for the **DocuVault**
module (`src`).

One source of truth (the code graph), one readable intermediate (the flow
model), three rendered surfaces:

```
  SOURCE OF TRUTH                       RENDERED SURFACES
  graphify-out/graph.json  ──►  flows.json ──►  1. Interactive living docs   (docs/interactive/)   non-tech
  (Graphify: files,             (curated    ──►  2. Confluence pages          (prose + Mermaid)      support / QA / PM
   symbols, edges,               "stories")  ──►  3. Machine context           (graphify wiki / MCP)  AI assistants
   communities)
```

- **Context layer** — `graphify-out/graph.json`, a NetworkX node-link graph of
  files, symbols and call/reference edges grouped into communities. Built once,
  updated incrementally.
- **Flow model** — `flows.json`, a curated set of *stories*: ordered steps
  through the graph, each with actors (the components it crosses), a
  plain-language `say` and a technical `tech` caption. This is the contract both
  renderers consume, and what turns a raw graph into a narrated walkthrough.
- **Three surfaces**, all generated from graph + flows.

## Files

| File | Role |
|------|------|
| `config.json` | Single source of paths/settings (module root, output dirs, extraction knobs). |
| `c2d_common.py` | Shared helpers: config/graph loading, version parsing, narration glossary. |
| `extract_flows.py` | **Bootstrap.** Graph → candidate flows (find entry points, walk call edges, narrate). |
| `flow_overrides.json` | Editorial titles/descriptions merged into generated flows (the "LLM pass", reproducible). |
| `flows.json` | **THE flow model** (committed). |
| `map_impact.py` | **Update.** Changed files → impacted flows + edge deltas; applies the diff→highlight plan to `flows.json`. |
| `redraft_prompt.md` | Drift-aware agent instructions — re-narrates impacted flows (`claude -p`). |
| `render_interactive.py` | `flows.json` → self-contained animated living-doc HTML (`docs/interactive/`). |
| `render_release_digest.py` | Diff → plain-English "what changed" (`docs/RELEASE_NOTES.md`). |
| `confluence_sync.py` | Flows → Confluence pages (prose + Mermaid); dry-run preview when secrets absent. |
| `.confluence_map.json` | `flowId → Confluence pageId` (committed). |

Transient (git-ignored): `impacted.json`, `.confluence_preview/`, `changed.txt`, `base-graph.json`.

## Bootstrap (one-time, per module)

```bash
# 1. Build the context layer (code is AST-only — no API key needed)
graphify "src" --wiki                            # -> graphify-out/

# 2. Extract the flow model
python code2docs/extract_flows.py                # -> code2docs/flows.json

# 3. Render the three surfaces
python code2docs/render_interactive.py           # -> docs/interactive/
python code2docs/render_release_digest.py --bootstrap --version 1.2.0.0   # -> docs/RELEASE_NOTES.md
python code2docs/confluence_sync.py --dry-run    # -> preview (or publishes if CONFLUENCE_* set)
```

Open `docs/interactive/index.html` to browse the living docs. Everything is
self-contained (inline CSS/JS) and publishable to GitHub Pages as-is.

## Post-merge update (automatic)

`.github/workflows/code2docs.yml` runs on merge to `main`:

1. `git diff` the merge → `changed.txt`; snapshot the base `graph.json`.
2. `graphify update` — re-extract only the changed files.
3. `map_impact.py` — changed files → impacted flows; diff edges; **apply the
   highlight plan** (an added edge on a flow's path becomes a new step tagged
   with the version; a removed/changed edge marks a step changed).
4. `redraft_prompt.md` via `claude -p` — re-narrate the impacted flows
   (best-effort; the deterministic highlights already stand alone).
5. Re-render the three surfaces **scoped to the impacted flows**.
6. Open a **review PR** (never a push to `main`) with the updated docs and
   Confluence drafts labelled `code2docs-review`.

The visual payoff: a merge that adds a call makes a flow visibly gain a
highlighted step — in the living doc (toggle "Highlight what changed") and the
Mermaid diagram — plus a one-line entry in the release digest.

## Secrets (GitHub repo settings)

- `ANTHROPIC_API_KEY` — for the drift-aware re-narration step (optional; skipped if unset).
- `CONFLUENCE_BASE_URL`, `CONFLUENCE_USER`, `CONFLUENCE_API_TOKEN`, `CONFLUENCE_SPACE_KEY`
  — for live Confluence publishing (optional; dry-run preview if unset).

No key is needed for the code graph itself — Java is extracted structurally (AST).

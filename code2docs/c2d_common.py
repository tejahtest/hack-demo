"""Shared helpers for the Code2Docs pipeline.

Every script (extract_flows, map_impact, render_interactive,
render_release_digest, confluence_sync) loads config and the graph through
here so path conventions and graph field names live in exactly one place.

graph.json is NetworkX node-link JSON:
  - nodes: {id, label, source_file, source_location, community, file_type, ...}
      source_file is RELATIVE to the module root (e.g. "main/Foo.cpp").
  - links: {source, target, relation, confidence, source_file, source_location, weight}
      relation is one of: calls | references | contains | imports
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


def init_io() -> None:
    """Force UTF-8 stdout/stderr so prints never crash on a cp1252 console
    (Windows). No-op where already UTF-8 (Linux CI)."""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
        except Exception:
            pass

# code2docs/ lives at <repo>/code2docs; the repo root is its parent.
CODE2DOCS_DIR = Path(__file__).resolve().parent
REPO_ROOT = CODE2DOCS_DIR.parent


def load_config(path: str | Path | None = None) -> dict:
    cfg_path = Path(path) if path else CODE2DOCS_DIR / "config.json"
    with open(cfg_path, encoding="utf-8") as fh:
        return json.load(fh)


def _abs(rel: str) -> Path:
    """Resolve a repo-relative path from config against the repo root."""
    p = Path(rel)
    return p if p.is_absolute() else REPO_ROOT / p


def load_graph(cfg: dict, graph_path: str | Path | None = None) -> dict:
    gp = Path(graph_path) if graph_path else _abs(cfg["graph_path"])
    with open(gp, encoding="utf-8") as fh:
        g = json.load(fh)
    # Normalise: expose edges under a stable key regardless of node-link naming.
    g["_edges"] = g.get("links", g.get("edges", []))
    g["_nodes_by_id"] = {n["id"]: n for n in g.get("nodes", [])}
    return g


def read_version(cfg: dict) -> str:
    """Best-effort product version, e.g. '3.11.3.0'. Falls back to '0.0'."""
    header = _abs(cfg.get("version_header", ""))
    if header.exists():
        text = header.read_text(encoding="utf-8", errors="ignore")
        m = re.search(r'_STRING\s+"([\d.]+)"', text)
        if m:
            return m.group(1)
        m = re.search(r"PRODUCTVERSION\s+([\d,]+)", text)
        if m:
            return m.group(1).replace(",", ".")
    return "0.0"


def short_version(version: str) -> str:
    """'3.11.3.0' -> '3.11' (major.minor is what a release digest shows)."""
    parts = version.split(".")
    return ".".join(parts[:2]) if len(parts) >= 2 else version


# ---- text helpers -------------------------------------------------------

_CAMEL = re.compile(r"(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])")


def readable(label: str) -> str:
    """Turn a code symbol into a human phrase.

    'handleUploadDocument()' -> 'upload document'
    'validateFileName()' -> 'validate file name'
    """
    name = label.strip()
    name = re.sub(r"\(.*?\)$", "", name).strip()      # drop trailing ()
    name = name.lstrip(".")                            # drop graphify leading-dot method notation
    name = name.rsplit(".", 1)[-1]                     # keep the method name if qualified (Class.method)
    name = re.sub(r"^handle(?=[A-Z])", "", name)       # drop controller 'handle' prefix
    words = _CAMEL.sub(" ", name).replace("_", " ").split()
    if not words:
        return label
    return " ".join(w if w.isupper() else w.lower() for w in words)


def short_label(label: str) -> str:
    """Bare method name for a diagram caption: '.buildComplianceReport()' -> 'buildComplianceReport'."""
    name = re.sub(r"\(.*?\)$", "", label.strip()).strip()
    name = name.lstrip(".").rsplit(".", 1)[-1]
    return name or label.strip()


def slugify(text: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    return s or "flow"


# First-word verb -> present-tense narration verb, for a readable `say` line.
_VERB = {
    "get": "Looks up", "is": "Checks", "are": "Checks", "does": "Checks",
    "do": "Checks", "has": "Checks", "register": "Registers",
    "unregister": "Removes the registration for", "create": "Creates",
    "delete": "Deletes", "remove": "Removes", "clear": "Clears",
    "init": "Sets up", "initialize": "Sets up", "set": "Sets",
    "format": "Builds", "verify": "Verifies", "launch": "Launches",
    "repair": "Repairs", "load": "Loads", "save": "Saves", "open": "Opens",
    "read": "Reads", "write": "Writes", "add": "Adds", "update": "Updates",
    "install": "Installs", "uninstall": "Uninstalls", "terminate": "Shuts down",
    "start": "Starts", "stop": "Stops", "expand": "Expands", "type": "Checks",
    "upload": "Uploads", "protect": "Protects", "share": "Shares",
    "revoke": "Revokes", "grant": "Grants", "encrypt": "Encrypts",
    "decrypt": "Decrypts", "rotate": "Rotates", "destroy": "Destroys",
    "generate": "Generates", "build": "Builds", "send": "Sends",
    "check": "Checks", "hash": "Hashes", "evaluate": "Evaluates",
    "record": "Records", "store": "Stores", "retrieve": "Fetches",
    "append": "Appends", "find": "Looks up", "validate": "Validates",
    "scrub": "Scrubs", "deliver": "Delivers", "mark": "Marks",
    "handle": "Handles", "emit": "Emits",
}

# First-word verb -> gerund, for a flow title.
_GERUND = {
    "install": "Installing", "uninstall": "Uninstalling", "repair": "Repairing",
    "get": "Getting", "startup": "Starting up", "shutdown": "Shutting down",
    "is": "Checking", "register": "Registering", "unregister": "Unregistering",
    "initialize": "Initializing", "verify": "Verifying", "launch": "Launching",
    "upload": "Uploading", "open": "Opening", "delete": "Deleting",
    "share": "Sharing", "revoke": "Revoking", "generate": "Generating",
    "protect": "Protecting", "grant": "Granting", "encrypt": "Encrypting",
    "decrypt": "Decrypting",
}


# Domain glossary: expand abbreviations and restore proper-noun casing in the
# human-facing prose. Applied to `say`/`title` text only (never to IDs).
_GLOSSARY = [
    (r"\bdocu vault\b", "DocuVault"),
    (r"\bdocuvault\b", "DocuVault"),
    (r"\baes\b", "AES"),
    (r"\bgcm\b", "GCM"),
    (r"\bsha\b", "SHA"),
    (r"\bacl\b", "ACL"),
    (r"\bid\b", "ID"),
    (r"\burl\b", "URL"),
    (r"\bapi\b", "API"),
    (r"\bemail\b", "email"),
]


def humanize(phrase: str) -> str:
    out = phrase
    for pat, rep in _GLOSSARY:
        out = re.sub(pat, rep, out, flags=re.IGNORECASE)
    return out


def action_phrase(label: str) -> str:
    """A one-line, present-tense description of what calling `label` does."""
    words = readable(label).split()
    if not words:
        return label
    head, rest = words[0], humanize(" ".join(words[1:]))
    if head == "log":
        if not rest:
            return "Writes a log line."
        art = "an" if rest[:1].lower() in "aeiou" else "a"
        return f"Writes {art} {rest} log line."
    verb = _VERB.get(head)
    if verb:
        return (f"{verb} {rest}." if rest else f"{verb}.").replace("  ", " ")
    phrase = humanize(readable(label))
    return phrase[:1].upper() + phrase[1:] + "."


def gerund_title(label: str) -> str:
    """A flow title from the entry-point label, e.g. IInstallW() -> 'Installing'."""
    words = readable(label).split()
    if not words:
        return label
    head, rest = words[0], humanize(" ".join(words[1:]))
    g = _GERUND.get(head)
    if g:
        return f"{g} {rest}".strip()
    phrase = humanize(readable(label))
    return phrase[:1].upper() + phrase[1:]


def is_function(node: dict) -> bool:
    """Function-like node (has a call signature) vs a bare type/variable node."""
    return node.get("label", "").rstrip().endswith(")")


# Emoji chosen per lane by keyword, so the sequence diagram reads at a glance.
_EMOJI_RULES = [
    (("crypto", "cipher", "encrypt", "decrypt", "key"), "🔐"),
    (("repository", "store", "storage"), "🗄️"),
    (("audit", "compliance", "report"), "📋"),
    (("notification", "email", "invite"), "✉️"),
    (("policy", "access", "permission"), "🛡️"),
    (("controller", "api"), "⚙️"),
    (("service", "logic"), "🧠"),
    (("model", "domain", "entity"), "🗂️"),
    (("document", "vault"), "📄"),
    (("user", "account"), "👤"),
    (("log", "config", "util", "validator"), "📝"),
]


def emoji_for(name: str) -> str:
    low = name.lower()
    for keys, emoji in _EMOJI_RULES:
        if any(k in low for k in keys):
            return emoji
    return "📦"


def derive_community_labels(graph: dict) -> dict:
    """community id -> readable lane name, from the dominant class (source file)
    of its function nodes. Deterministic (no LLM/API key), and distinct per lane
    (class names rarely collide, unlike folders). Used when graphify emitted no
    .graphify_labels.json, so lanes read as 'AuditService'/'KeyManager' rather
    than 'Component 3'. Accepts a full graph or a {"_nodes_by_id": {...}} wrapper.
    """
    import collections
    classes = collections.defaultdict(collections.Counter)
    for node in graph.get("_nodes_by_id", {}).values():
        cid = node.get("community")
        if cid is None or not is_function(node):
            continue
        sf = (node.get("source_file") or "").replace("\\", "/")
        base = sf.rsplit("/", 1)[-1]
        cls = re.sub(r"\.[A-Za-z0-9]+$", "", base)  # strip extension -> class name
        if cls:
            classes[cid][cls] += 1
    labels = {}
    for cid, counter in classes.items():
        if counter:
            labels[cid] = counter.most_common(1)[0][0]
    return labels

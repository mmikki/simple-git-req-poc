#!/usr/bin/env python3
"""
Build a traceability graph by parsing requirement files (YAML front matter)
and scanning code / test sources for requirement annotations.

Outputs: JSON graph -> `outputs/trace.json`

Model:
- Requirements are Markdown files with YAML front matter (mandatory).
- Links in front matter are optional and copied verbatim into the graph.
- Code / tests may reference requirements using one of these patterns:
    - "REQ: <ID>"
    - "@REQ(<ID>)"
"""

from __future__ import annotations

import json
import os
import re
import sys
from dataclasses import asdict, dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

# ---- Third-party dependency (mandatory) --------------------------------------

try:
    import yaml  # PyYAML
    from yaml.loader import SafeLoader
except ImportError:
    print("[ERROR] PyYAML is required. Install with: pip install pyyaml", file=sys.stderr)
    sys.exit(1)

# ---- Configuration ------------------------------------------------------------
# If True, disable YAML implicit timestamp parsing so values like "2025-12-17"
# remain plain strings instead of datetime.date. You can override via env:
#   TRACE_YAML_NO_DATES=0 or 1
USE_NO_DATES_LOADER: bool = os.environ.get("TRACE_YAML_NO_DATES", "1").strip() not in {
    "0",
    "false",
    "False",
}

# ---- Optional loader with timestamps disabled --------------------------------


class NoDatesSafeLoader(SafeLoader):
    """SafeLoader variant that keeps date-like scalars as strings."""


if USE_NO_DATES_LOADER:
    # Remove implicit resolver for timestamps so they are kept as strings.
    # Works across PyYAML versions that differ in resolver tuple shapes.
    TIMESTAMP_TAG = "tag:yaml.org,2002:timestamp"

    # Iterate over implicit resolvers and filter out timestamp resolvers.
    for ch, resolvers in list(NoDatesSafeLoader.yaml_implicit_resolvers.items()):
        filtered = []
        for entry in resolvers:
            # Entries can be (tag, regexp) or (tag, regexp, first)
            if isinstance(entry, tuple) and entry:
                tag = entry[0]
                if tag == TIMESTAMP_TAG:
                    # Skip timestamp resolvers
                    continue
            filtered.append(entry)
        NoDatesSafeLoader.yaml_implicit_resolvers[ch] = filtered

# ---- Constants ----------------------------------------------------------------

FRONT_MATTER_RE: re.Pattern[str] = re.compile(r"^---\n(.*?)\n---\n", re.S)

DEFAULT_SOURCE_ROOTS: Tuple[str, ...] = ("src", "tests", "examples")

# Files we consider "text" for annotation scanning
SCAN_SUFFIXES: Tuple[str, ...] = (".py", ".ts", ".js", ".cpp", ".c", ".md", ".txt")

# Annotation patterns to find requirement IDs in text sources
ANNOTATION_PATTERNS: Tuple[re.Pattern[str], ...] = (
    re.compile(r"REQ:\s*([A-Za-z0-9_-]+)"),
    re.compile(r"@REQ\(([^)]+)\)"),
)

# Requirement roots
REQ_ROOTS: Tuple[Path, ...] = (
    Path("requirements/business"),
    Path("requirements/system"),
    Path("requirements/software"),
    Path("verification/requirements"),
)

# ---- Data structures ----------------------------------------------------------


@dataclass
class Requirement:
    """A single requirement parsed from a Markdown file with YAML front matter."""

    id: str
    path: str
    meta: Dict[str, object]  # full front-matter dict (title, level, status, links, etc.)


@dataclass
class Annotation:
    """A single annotation occurrence found in a source file."""

    id: str
    file: str
    line: int


@dataclass
class TraceGraph:
    """Traceability graph suitable for JSON serialization."""

    requirements: Dict[str, Dict[str, object]]  # id -> front matter (plus path)
    annotations: List[Annotation]
    links: List[Dict[str, str]]  # normalized links: {from, type, to}


# ---- Parsing helpers ----------------------------------------------------------


def read_front_matter(text: str) -> Tuple[Optional[Dict[str, object]], str]:
    """
    Parse YAML front matter and return (front_matter_dict, markdown_body).
    If no front matter, returns (None, original_text).
    Raises ValueError if YAML is present but invalid.
    """
    match = FRONT_MATTER_RE.match(text)
    if not match:
        return None, text

    raw = match.group(1)
    body = text[match.end() :]
    try:
        if USE_NO_DATES_LOADER:
            data = yaml.load(raw, Loader=NoDatesSafeLoader) or {}
        else:
            data = yaml.safe_load(raw) or {}
    except yaml.YAMLError as exc:
        raise ValueError(f"Invalid YAML front matter: {exc}") from exc

    if not isinstance(data, dict):
        raise ValueError("Front matter must be a YAML mapping (key: value).")

    return data, body


def iter_requirement_files(roots: Iterable[Path]) -> Iterable[Path]:
    """Yield requirement Markdown files under the given roots."""
    for root in roots:
        if not root.exists():
            continue
        yield from sorted(root.glob("**/*.md"))


def load_requirements() -> Dict[str, Requirement]:
    """
    Load all requirement files and return a mapping: id -> Requirement.
    Front matter is mandatory; missing or malformed front matter raises ValueError.
    """
    req_index: Dict[str, Requirement] = {}

    for file_path in iter_requirement_files(REQ_ROOTS):
        text = file_path.read_text(encoding="utf-8")
        fm, _body = read_front_matter(text)
        if fm is None:
            raise ValueError(f"Missing YAML front matter in: {file_path}")

        rid = str(fm.get("id") or "").strip()
        if not rid:
            raise ValueError(f"Missing 'id' in front matter: {file_path}")

        if rid in req_index:
            prev = req_index[rid].path
            raise ValueError(
                f"Duplicate requirement id '{rid}' in {file_path} (already seen in {prev})"
            )

        meta: Dict[str, object] = dict(fm)
        meta["_path"] = str(file_path)

        req_index[rid] = Requirement(id=rid, path=str(file_path), meta=meta)

    return req_index


# ---- Annotation scanning ------------------------------------------------------


def find_annotations(source_roots: Optional[Iterable[str]] = None) -> List[Annotation]:
    """
    Scan source roots for requirement annotations and return a list of Annotation entries.
    """
    roots = list(source_roots or DEFAULT_SOURCE_ROOTS)
    results: List[Annotation] = []

    for root_str in roots:
        root = Path(root_str)
        if not root.exists():
            continue

        for f in root.glob("**/*"):
            if not (f.is_file() and f.suffix in SCAN_SUFFIXES):
                continue

            try:
                text = f.read_text(encoding="utf-8")
            except Exception:
                # Skip unreadable files silently
                continue

            for pat in ANNOTATION_PATTERNS:
                for match in pat.finditer(text):
                    rid = match.group(1).strip()
                    line_no = text.count("\n", 0, match.start()) + 1
                    results.append(Annotation(id=rid, file=str(f), line=line_no))

    return results


# ---- Link normalization -------------------------------------------------------


def normalize_links(requirements: Dict[str, Requirement]) -> List[Dict[str, str]]:
    """
    Collect and normalize links from the front matter of each requirement.

    Front matter typically has:
      links:
        key1: [TARGET_ID, ...]
        key2: TARGET_ID

    We normalize into: {"from": <rid>, "type": <key>, "to": <target_id>}
    """
    normalized: List[Dict[str, str]] = []

    for req in requirements.values():
        links = req.meta.get("links", [])
        if isinstance(links, dict):
            link_items = [links]
        elif isinstance(links, list):
            link_items = links
        else:
            link_items = []

        for link in link_items:
            if not isinstance(link, dict):
                # Skip malformed link entries
                continue

            for key, targets in link.items():
                # Allow scalar or list
                if isinstance(targets, list):
                    target_list = targets
                else:
                    target_list = [targets]

                for target in target_list:
                    if target is None:
                        continue
                    normalized.append({"from": req.id, "type": str(key), "to": str(target)})

    return normalized


# ---- JSON sanitizer -----------------------------------------------------------


def _sanitize(obj: object) -> object:
    """
    Recursively convert non-JSON-serializable types to safe representations.
    - datetime/date -> ISO 8601 strings
    - Path -> str
    - set/tuple -> list
    - dict keys forced to str, values sanitized
    """
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    if isinstance(obj, Path):
        return str(obj)
    if isinstance(obj, dict):
        return {str(k): _sanitize(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set)):
        return [_sanitize(v) for v in obj]
    # Primitives (str, int, float, bool, None) are OK as-is
    return obj


# ---- Build graph --------------------------------------------------------------


def build_graph() -> TraceGraph:
    """Build the trace graph from requirements and annotations."""
    requirements = load_requirements()
    annotations = find_annotations()
    links = normalize_links(requirements)

    # Prepare payload for JSON
    reqs_payload: Dict[str, Dict[str, object]] = {
        rid: dict(req.meta)  # includes _path and all front-matter
        for rid, req in requirements.items()
    }

    return TraceGraph(
        requirements=reqs_payload,
        annotations=annotations,
        links=links,
    )


# ---- CLI ----------------------------------------------------------------------


def main() -> None:
    """Entry point; writes `outputs/trace.json`."""
    output_path = Path("outputs/trace.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        graph = build_graph()
    except Exception as exc:
        print(f"[FAIL] Traceability build failed: {exc}", file=sys.stderr)
        sys.exit(1)

    # Convert dataclasses to dicts and sanitize non-JSON types
    payload = {
        "requirements": graph.requirements,
        "annotations": [asdict(a) for a in graph.annotations],
        "links": graph.links,
    }
    safe_payload = _sanitize(payload)

    output_path.write_text(
        json.dumps(safe_payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"[OK] Wrote {output_path}")


if __name__ == "__main__":
    main()

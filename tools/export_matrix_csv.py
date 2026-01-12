#!/usr/bin/env python3
"""
Export a simple traceability matrix (CSV) from `outputs/trace.json`.

Columns:
- id
- title
- level
- status
- parent              (comma-separated)
- verifies            (comma-separated)
- annotated_locations (file:line entries separated by ' | ')

Notes:
- 'parent' and 'verifies' are extracted from the requirement's front-matter links.
- Annotated locations come from the trace builder's scanning results.
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

from common import extract_link_targets, load_trace

TRACE_JSON_PATH = Path("outputs/trace.json")
CSV_OUT_PATH = Path("outputs/traceability.csv")


def _build_annotation_index(annotations: Iterable[Dict[str, object]]) -> Dict[str, List[str]]:
    """
    Build an index: requirement_id -> [ "file:line", ... ]

    Args:
        annotations: list of {"id": <rid>, "file": <path>, "line": <int>}

    Returns:
        dict mapping requirement id to list of file:line strings.
    """
    idx: Dict[str, List[str]] = {}
    for a in annotations:
        rid = str(a.get("id", "")).strip()
        if not rid:
            continue
        file = str(a.get("file", "")).strip()
        try:
            line = int(a.get("line", 0))  # type: ignore[call-overload]
        except (TypeError, ValueError):
            line = 0
        loc = f"{file}:{line}" if file else ""
        if not loc:
            continue
        idx.setdefault(rid, []).append(loc)
    return idx


def _comma_join(values: Iterable[str]) -> str:
    """Join non-empty values by comma, or return empty string."""
    vals = [v for v in (str(x).strip() for x in values) if v]
    return ",".join(vals) if vals else ""


def _iter_requirements_in_order(
    reqs: Dict[str, Dict[str, object]],
) -> List[Tuple[str, Dict[str, object]]]:
    """
    Return a stable list of (id, req_meta) sorted by:
    1) level (business, system, software, verification),
    2) id (lexicographically).

    If 'level' is missing or unknown, it sorts last.
    """
    order = {"business": 0, "system": 1, "software": 2, "verification": 3}

    def sort_key(item: Tuple[str, Dict[str, object]]) -> Tuple[int, str]:
        rid, meta = item
        lvl = str(meta.get("level", "")).strip().lower()
        lvl_rank = order.get(lvl, 99)
        return (lvl_rank, rid)

    return sorted(reqs.items(), key=sort_key)


def _write_csv(
    reqs: Dict[str, Dict[str, object]],
    annotations_idx: Dict[str, List[str]],
    out_path: Path,
) -> None:
    """
    Write the CSV to `out_path` using the fixed column set.
    """
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with out_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(
            ["id", "title", "level", "status", "parent", "verifies", "annotated_locations"]
        )

        for rid, meta in _iter_requirements_in_order(reqs):
            title = str(meta.get("title", "")).strip()
            level = str(meta.get("level", "")).strip()
            status = str(meta.get("status", "")).strip()
            links = meta.get("links", []) or []

            parents = extract_link_targets(links, "parent")
            verifies = extract_link_targets(links, "verifies")
            ann_locs = annotations_idx.get(rid, [])

            writer.writerow(
                [
                    rid,
                    title,
                    level,
                    status,
                    _comma_join(parents),
                    _comma_join(verifies),
                    " | ".join(sorted(set(ann_locs))),
                ]
            )


def main() -> None:
    """CLI entry point."""
    try:
        trace = load_trace()
    except FileNotFoundError:
        print(
            f"[FAIL] Missing {TRACE_JSON_PATH} (run build_traceability.py first).", file=sys.stderr
        )
        sys.exit(1)
    except json.JSONDecodeError as exc:
        print(f"[FAIL] Malformed JSON in {TRACE_JSON_PATH}: {exc}", file=sys.stderr)
        sys.exit(1)

    reqs = trace.get("requirements", {}) or {}
    annotations = trace.get("annotations", []) or []

    if not isinstance(reqs, dict):
        print("[FAIL] 'requirements' in trace is not a mapping.", file=sys.stderr)
        sys.exit(1)
    if not isinstance(annotations, list):
        print("[FAIL] 'annotations' in trace is not a list.", file=sys.stderr)
        sys.exit(1)

    idx = _build_annotation_index(annotations)

    try:
        _write_csv(reqs, idx, CSV_OUT_PATH)
    except Exception as exc:
        print(f"[FAIL] CSV export failed: {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"[OK] Wrote {CSV_OUT_PATH}")


if __name__ == "__main__":
    main()

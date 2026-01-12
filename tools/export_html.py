#!/usr/bin/env python3
"""
Export a traceability matrix as HTML from `outputs/trace.json`.

Columns rendered:
- ID
- Title
- Level
- Status
- Derives From         (front-matter `derives` + incoming `derives` from normalized links)
- Satisfies            (front-matter `satisfies`)
- Verified By (TRQ)    (front-matter `verified_by`)
- Tested By (TC)       (computed via TRQ -> tested_by from normalized links)
- Verifies (on TRQ)    (front-matter `verifies`)

This mirrors Model A:
- Requirement (BR/SR/TR) -> TRQ via verified_by
- TRQ -> Requirement via verifies
- TRQ -> Test Case via tested_by
"""

from __future__ import annotations

import json
import sys
from html import escape
from pathlib import Path
from typing import Dict, Iterable, List, Set, Tuple

from common import extract_link_targets, load_trace

TRACE_JSON_PATH = Path("outputs/trace.json")
HTML_OUT_PATH = Path("outputs/traceability.html")


# ----------------------------- helpers ----------------------------------------


def _iter_requirements_in_order(
    reqs: Dict[str, Dict[str, object]],
) -> List[Tuple[str, Dict[str, object]]]:
    """Sort requirements by ID for consistent output."""
    return sorted(reqs.items(), key=lambda kv: kv[0])


def _incoming_derives(current_id: str, normalized_links: Iterable[Dict[str, object]]) -> List[str]:
    """
    Find all requirements that have 'derives' links pointing TO current_id.
    Returns a sorted list of IDs.
    """
    incoming = set()
    for link in normalized_links:
        if link.get("type") == "derives" and link.get("to") == current_id:
            from_id = link.get("from")
            if from_id:
                incoming.add(from_id)
    return sorted(incoming)  # type: ignore[arg-type]


def _tested_by_tc_for_requirement(
    rid: str,
    reqs: Dict[str, Dict[str, object]],
    normalized_links: List[Dict[str, object]],
) -> List[str]:
    """
    For a given requirement, find the test cases that test it via TRQ.
    Logic: requirement -> verified_by -> TRQ -> tested_by -> TC
    """
    tc_set: Set[str] = set()
    meta = reqs.get(rid, {})
    verified_by_trq = extract_link_targets(meta.get("links", []), "verified_by")

    if not verified_by_trq:
        return []

    trq_lookup = set(verified_by_trq)
    for link in normalized_links:
        if link.get("type") == "tested_by" and link.get("from") in trq_lookup:
            tc = link.get("to")
            if tc:
                tc_set.add(tc)  # type: ignore[arg-type]

    return sorted(tc_set)


# ----------------------------- HTML -------------------------------------------


def _render_html_table(
    reqs: Dict[str, Dict[str, object]],
    normalized_links: List[Dict[str, object]],
) -> str:
    """Build an HTML table for all requirements."""
    rows: List[str] = []

    for rid, meta in _iter_requirements_in_order(reqs):
        title = str(meta.get("title", "")).strip()
        level = str(meta.get("level", "")).strip()
        status = str(meta.get("status", "")).strip()

        links = meta.get("links", {}) or {}

        derives_from = extract_link_targets(links, "derives")
        satisfies = extract_link_targets(links, "satisfies")
        depends_on = extract_link_targets(links, "depends_on")
        verified_by = extract_link_targets(links, "verified_by")
        tested_by = _tested_by_tc_for_requirement(rid, reqs, normalized_links)
        verifies = extract_link_targets(links, "verifies")

        rows.append(
            f"<tr>"
            f"<td>{escape(rid)}</td>"
            f"<td>{escape(title)}</td>"
            f"<td>{escape(level)}</td>"
            f"<td>{escape(status)}</td>"
            f"<td>{escape(', '.join(derives_from))}</td>"
            f"<td>{escape(', '.join(satisfies))}</td>"
            f"<td>{escape(', '.join(depends_on))}</td>"
            f"<td>{escape(', '.join(verified_by))}</td>"
            f"<td>{escape(', '.join(tested_by))}</td>"
            f"<td>{escape(', '.join(verifies))}</td>"
            f"</tr>"
        )

    return "\n".join(rows)


def main() -> None:
    """CLI entry point."""
    try:
        trace = load_trace()
    except FileNotFoundError:
        print(f"[FAIL] Missing {TRACE_JSON_PATH}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as exc:
        print(f"[FAIL] Malformed JSON: {exc}", file=sys.stderr)
        sys.exit(1)

    reqs = trace.get("requirements", {}) or {}
    norm_links = trace.get("links", []) or []

    table_rows = _render_html_table(reqs, norm_links)

    html = f"""<!doctype html>
<html><head><meta charset='utf-8'><title>Traceability</title>
<style>
table{{border-collapse:collapse;width:100%;}}
td,th{{border:1px solid #ccc;padding:8px;text-align:left;}}
th{{background:#f0f0f0;}}
body{{font-family:sans-serif;margin:20px;}}
</style></head><body>
<h1>Traceability Matrix</h1>
<table>
<thead><tr><th>ID</th><th>Title</th><th>Level</th><th>Status</th><th>Derives From</th><th>Satisfies</th><th>Depends On</th><th>Verified By (TRQ)</th><th>Tested By (TC)</th><th>Verifies</th></tr></thead>  # noqa: E501
<tbody>{table_rows}</tbody>
</table>
</body></html>
"""

    HTML_OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    HTML_OUT_PATH.write_text(html, encoding="utf-8")
    print(f"[OK] Wrote {HTML_OUT_PATH}")


if __name__ == "__main__":
    main()

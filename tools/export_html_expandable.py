#!/usr/bin/env python3
"""
Export an expandable traceability matrix as HTML from `outputs/trace.json`.

Business requirements are expandable to show their derived system/software/
verification requirements.
"""

from __future__ import annotations

import json
import sys
from html import escape
from pathlib import Path
from typing import Dict, List, Set

from common import extract_link_targets, load_trace

TRACE_JSON_PATH = Path("outputs/trace.json")
HTML_OUT_PATH = Path("outputs/traceability_expandable.html")


def _get_test_cases(
    req_id: str,
    reqs: Dict[str, Dict[str, object]],
    normalized_links: List[Dict[str, object]],
) -> List[str]:
    """Get test cases for a requirement via TRQ -> tested_by links."""
    tc_set: Set[str] = set()

    # Get TRQs that verify this requirement
    meta = reqs.get(req_id, {})
    verified_by_trq = extract_link_targets(meta.get("links", []), "verified_by")

    if not verified_by_trq:
        return []

    # Find test cases linked to those TRQs
    trq_lookup = set(verified_by_trq)
    for link in normalized_links:
        if link.get("type") == "tested_by" and link.get("from") in trq_lookup:
            tc = link.get("to")
            if tc:
                tc_set.add(tc)  # type: ignore[arg-type]

    return sorted(tc_set)


def _get_derives_from(
    req_id: str,
    reqs: Dict[str, Dict[str, object]],
) -> List[str]:
    """Get what this requirement derives from (from front matter)."""
    meta = reqs.get(req_id, {})
    links = meta.get("links", {}) or {}

    derives_list = []
    if isinstance(links, dict):
        derives = links.get("derives", [])
        if isinstance(derives, list):
            derives_list = derives
        elif derives:
            derives_list = [derives]

    return sorted(derives_list)


def _get_derived_children(
    parent_id: str,
    reqs: Dict[str, Dict[str, object]],
) -> Dict[str, List[str]]:
    """
    Find all requirements that derive from parent_id by checking their
    'derives' field.

    Returns dict with levels as keys:
    {'system': [...], 'software': [...], 'verification': [...]}
    """
    tree: dict[str, list[str]] = {
        "system": [],
        "software": [],
        "verification": [],
    }

    # Look through all requirements to find ones that derive from this parent
    for rid, meta in reqs.items():
        if rid == parent_id:
            continue

        links = meta.get("links", {}) or {}
        derives_list = []

        # Extract derives targets
        if isinstance(links, dict):
            derives = links.get("derives", [])
            if isinstance(derives, list):
                derives_list = derives
            elif derives:
                derives_list = [derives]

        # If this requirement derives from our parent, add it to the tree
        if parent_id in derives_list:
            level = str(meta.get("level", "")).strip().lower()
            if level in tree:
                tree[level].append(rid)

                # Recursively find children of this requirement
                child_tree = _get_derived_children(rid, reqs)
                for lvl in tree:
                    tree[lvl].extend(child_tree[lvl])

    # Deduplicate while preserving order
    for level in tree:
        seen = set()
        deduped = []
        for item in tree[level]:
            if item not in seen:
                seen.add(item)
                deduped.append(item)
        tree[level] = deduped

    return tree


def _render_requirement_row(
    rid: str,
    meta: Dict[str, object],
    reqs: Dict[str, Dict[str, object]],
    normalized_links: List[Dict[str, object]],
    is_expandable: bool = False,
    indent_level: int = 0,
) -> str:
    """Render a single requirement row."""
    title = str(meta.get("title", "")).strip()
    level = str(meta.get("level", "")).strip()
    status = str(meta.get("status", "")).strip()
    links = meta.get("links", []) or {}

    derives_from = _get_derives_from(rid, reqs)
    satisfies = extract_link_targets(links, "satisfies")
    depends_on = extract_link_targets(links, "depends_on")
    verified_by = extract_link_targets(links, "verified_by")
    test_cases = _get_test_cases(rid, reqs, normalized_links)

    indent_style = f"padding-left:{20 + indent_level * 20}px" if indent_level > 0 else ""
    expand_class = "expandable" if is_expandable else ""
    expand_icon = "▶" if is_expandable else ""

    return (
        f"<tr class='req-row {expand_class}' data-req-id='{escape(rid)}'>"
        f"<td style='{indent_style}'>"
        f"<span class='expand-icon'>{expand_icon}</span> {escape(rid)}"
        f"</td>"
        f"<td>{escape(title)}</td>"
        f"<td>{escape(level)}</td>"
        f"<td>{escape(status)}</td>"
        f"<td>{escape(', '.join(derives_from))}</td>"
        f"<td>{escape(', '.join(satisfies))}</td>"
        f"<td>{escape(', '.join(depends_on))}</td>"
        f"<td>{escape(', '.join(verified_by))}</td>"
        f"<td>{escape(', '.join(test_cases))}</td>"
        "</tr>"
    )


def _render_html(
    reqs: Dict[str, Dict[str, object]],
    normalized_links: List[Dict[str, object]],
) -> str:
    """Render the full expandable HTML document."""
    rows: List[str] = []

    # Separate business requirements from others
    business_reqs = []

    for rid, meta in sorted(reqs.items()):
        level = str(meta.get("level", "")).strip().lower()
        if level == "business":
            business_reqs.append((rid, meta))

    # Render business requirements with their expandable children
    for rid, meta in business_reqs:
        rows.append(_render_requirement_row(rid, meta, reqs, normalized_links, is_expandable=True))

        # Get derived tree using the front-matter based approach
        tree = _get_derived_children(rid, reqs)

        # Render derived requirements (hidden by default)
        for level_name in ["system", "software", "verification"]:
            for child_id in tree[level_name]:
                if child_id in reqs:
                    child_meta = reqs[child_id]
                    indent = 1 if level_name == "system" else 2
                    row = _render_requirement_row(
                        child_id,
                        child_meta,
                        reqs,
                        normalized_links,
                        indent_level=indent,
                    )
                    parent_attr = f"data-parent='{escape(rid)}'"
                    rows.append(
                        row.replace(
                            "<tr",
                            f"<tr class='child-row' {parent_attr} " f"style='display:none'",
                        )
                    )

    # Build table headers
    table_headers = (
        "<th>ID</th>"
        "<th>Title</th>"
        "<th>Level</th>"
        "<th>Status</th>"
        "<th>Derives From</th>"
        "<th>Satisfies</th>"
        "<th>Depends On</th>"
        "<th>Verified By (TRQ)</th>"
        "<th>Tested By (TC)</th>"
    )

    html = (
        """<!doctype html>
<html><head><meta charset='utf-8'><title>Expandable Traceability</title>
<style>
body{font-family:system-ui,Segoe UI,Roboto,Helvetica,Arial,sans-serif;margin:20px}
table{border-collapse:collapse;width:100%;}
td,th{border:1px solid #ddd;padding:8px;text-align:left}
th{background:#f8f8f8;position:sticky;top:0}
.expandable{cursor:pointer;background:#f5f5f5}
.expandable:hover{background:#e8e8e8}
.expand-icon{display:inline-block;width:16px;font-size:12px;transition:transform 0.2s}
.expanded .expand-icon{transform:rotate(90deg)}
.child-row{background:#fafafa}
tr:nth-child(even):not(.child-row){background:#f9f9f9}
h1{margin-bottom:10px}
</style>
</head><body>
<h1>Expandable Traceability Matrix</h1>
<p>Click on business requirements (▶) to expand and see derived requirements.</p>
<table>
<thead><tr>
"""
        + table_headers
        + """
</tr></thead>
<tbody>
"""
        + "\n".join(rows)
        + """
</tbody>
</table>
<script>
document.querySelectorAll('.expandable').forEach(row => {
    row.addEventListener('click', () => {
        const reqId = row.dataset.reqId;
        const children = document.querySelectorAll(`[data-parent="${reqId}"]`);
        const isExpanded = row.classList.contains('expanded');

        row.classList.toggle('expanded');
        children.forEach(child => {
            child.style.display = isExpanded ? 'none' : 'table-row';
        });
    });
});
</script>
</body></html>
"""
    )
    return html


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

    html = _render_html(reqs, norm_links)

    HTML_OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    HTML_OUT_PATH.write_text(html, encoding="utf-8")
    print(f"[OK] Wrote {HTML_OUT_PATH}")


if __name__ == "__main__":
    main()

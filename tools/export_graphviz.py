"""Export requirements to Graphviz DOT format."""

import json
import sys
from pathlib import Path

from common import load_trace

TRACE_JSON_PATH = Path("outputs/trace.json")


def _extract_link_list(links, key):
    """Extract link targets for a specific key."""
    if links is None or not isinstance(links, dict):
        return []

    val = links.get(key)
    if isinstance(val, list):
        return [str(v).strip() for v in val if v]
    if val:
        return [str(val).strip()]
    return []


def _node_id(req_id):
    """Convert a requirement ID to a valid Graphviz node ID."""
    return req_id.replace("-", "_")


def _render_nodes(reqs):
    """Render all requirement nodes."""
    for req_id in sorted(reqs.keys()):
        meta = reqs[req_id] or {}
        title = meta.get("title", "(untitled)")
        level = meta.get("level", "unknown")
        # status = meta.get("status", "unknown")  # Currently unused

        # Color by level
        color_map = {
            "business": "lightblue",
            "system": "lightgreen",
            "software": "lightyellow",
            "verification": "lightcoral",
        }
        color = color_map.get(level, "white")

        node_id = _node_id(req_id)
        label = f"{req_id}\\n{title}\\n[{level}]"

        yield f'    {node_id} [label="{label}", shape=box, style=filled, fillcolor={color}];'


def _render_edges(normalized_links):
    """Render edges for all links."""
    for link in normalized_links:
        link_type = link.get("type", "")
        source = link.get("from")
        target = link.get("to")

        if not source or not target:
            continue

        style_map = {
            "derives": "solid",
            "satisfies": "dashed",
            "verified_by": "dotted",
            "depends_on": "bold",
        }
        style = style_map.get(link_type, "solid")

        src_node = _node_id(source)
        tgt_node = _node_id(target)

        yield f'    {src_node} -> {tgt_node} [style={style}, label="{link_type}"];'


def _render_dot(reqs, normalized_links):
    """Render the complete DOT file."""
    lines = [
        "digraph requirements {",
        "    rankdir=LR;",
        '    node [fontname="Helvetica"];',
        '    edge [fontname="Helvetica"];',
        "",
    ]

    lines.extend(_render_nodes(reqs))
    lines.append("")
    lines.extend(_render_edges(normalized_links))

    lines.extend(
        [
            "",
            "}",
        ]
    )

    return "\n".join(lines)


def main():
    """Generate Graphviz DOT output."""
    try:
        trace = load_trace()
    except FileNotFoundError:
        print(
            f"[FAIL] Missing {TRACE_JSON_PATH} (run build_traceability.py first).",
            file=sys.stderr,
        )
        sys.exit(1)
    except json.JSONDecodeError as exc:
        print(f"[FAIL] Malformed JSON in {TRACE_JSON_PATH}: {exc}", file=sys.stderr)
        sys.exit(1)

    reqs = trace.get("requirements", {}) or {}
    links = trace.get("links", []) or []

    dot_output = _render_dot(reqs, links)

    output_path = Path("outputs/requirements.dot")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(dot_output, encoding="utf-8")

    print(f"[OK] Generated {output_path}")


if __name__ == "__main__":
    main()

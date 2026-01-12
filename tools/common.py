"""Shared utilities for requirement tools."""

import json
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

TRACE_JSON_PATH = Path("outputs/trace.json")

REQ_ROOTS: Tuple[Path, ...] = (
    Path("requirements/business"),
    Path("requirements/system"),
    Path("requirements/software"),
    Path("verification/requirements"),
)


def load_trace() -> Dict[str, Any]:
    """Load the JSON produced by build_traceability.py.

    Returns:
        Dictionary containing requirements and links data.

    Raises:
        SystemExit: If trace.json is missing or malformed.
    """
    try:
        text = TRACE_JSON_PATH.read_text(encoding="utf-8")
        return json.loads(text)  # type: ignore[no-any-return]
    except FileNotFoundError:
        print(
            f"[FAIL] Missing {TRACE_JSON_PATH} (run build_traceability.py first).",
            file=sys.stderr,
        )
        sys.exit(1)
    except json.JSONDecodeError as exc:
        print(
            f"[FAIL] Malformed JSON in {TRACE_JSON_PATH}: {exc}",
            file=sys.stderr,
        )
        sys.exit(1)


def extract_link_targets(links_block: Any, key: str) -> List[str]:
    """Extract targets for a specific link key from the 'links' block.

    Supports: dict or list[dict]. Returns a list of IDs (strings).

    Args:
        links_block: The links data structure (dict or list of dicts).
        key: The link type key to extract (e.g., 'derives', 'satisfies').

    Returns:
        List of target requirement IDs.
    """
    if links_block is None:
        return []

    targets: List[str] = []
    link_items: List[Dict[str, Any]] = []

    if isinstance(links_block, dict):
        link_items = [links_block]
    elif isinstance(links_block, list):
        link_items = [li for li in links_block if isinstance(li, dict)]
    else:
        return []

    for entry in link_items:
        if key not in entry:
            continue
        val = entry[key]
        if isinstance(val, list):
            targets.extend(str(x).strip() for x in val if x is not None)
        else:
            targets.append(str(val).strip())

    return [v for v in targets if v]


def iter_requirement_files(roots: Iterable[Path]) -> Iterable[Path]:
    """Yield requirement Markdown files under the given roots.

    Args:
        roots: Iterable of directory paths to search.

    Yields:
        Path objects for each .md file found (excluding .bak files).
    """
    for root in roots:
        if not root.is_dir():
            continue
        for md_file in sorted(root.glob("*.md")):
            if not md_file.name.endswith(".bak"):
                yield md_file

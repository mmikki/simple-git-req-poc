#!/usr/bin/env python3
"""
Validate requirement documents and their links under Model A.

Model A semantics:
- Requirements (business/system/software) link to verification requirements via:
    - 'verified_by' (or 'covered_by' if present in the schema)
- Verification requirements (level: verification) link to:
    - 'verifies' -> business/system/software requirement IDs
    - 'tested_by' -> test case IDs (TC-xxx) under verification/test-cases

Additionally enforces:
- Required fields: id, title, status, level
- Enums: level, status
- ID patterns by level (from schema)
- Test case ID pattern (from schema)
- All link keys must be declared in schema.link_keys
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set, Tuple

# --- Third-party dependency (mandatory) ---------------------------------------

try:
    import yaml  # PyYAML
except ImportError:
    print("[ERROR] PyYAML is required. Install with: pip install pyyaml", file=sys.stderr)
    sys.exit(1)

# --- Regex for YAML front matter ----------------------------------------------

FRONT_MATTER_RE: re.Pattern[str] = re.compile(r"^---\n(.*?)\n---\n", re.S)

# --- Repository layout constants ----------------------------------------------

REQ_ROOTS: Tuple[Path, ...] = (
    Path("requirements/business"),
    Path("requirements/system"),
    Path("requirements/software"),
    Path("verification/requirements"),
)

TC_ROOTS: Tuple[Path, ...] = (Path("verification/test-cases"),)

# --- Data structures ----------------------------------------------------------


@dataclass(frozen=True)
class Schema:
    required: Set[str]
    enum_levels: Set[str]
    enum_status: Set[str]
    allowed_link_keys: Set[str]
    id_patterns: Dict[str, re.Pattern[str]]
    testcase_pattern: re.Pattern[str]
    # Optional alias key for req -> TRQ (in addition to 'verified_by')
    req_to_trq_aliases: Set[str]


# --- Helpers ------------------------------------------------------------------


def read_front_matter(text: str) -> Tuple[Optional[Dict[str, object]], str]:
    """
    Parse YAML front matter and return (front_matter_dict, markdown_body).
    If no front matter, returns (None, original_text).
    Raises ValueError if YAML is present but invalid or not a mapping.
    """
    match = FRONT_MATTER_RE.match(text)
    if not match:
        return None, text

    raw = match.group(1)
    body = text[match.end() :]

    try:
        data = yaml.safe_load(raw) or {}
    except yaml.YAMLError as exc:
        raise ValueError(f"Invalid YAML front matter: {exc}") from exc

    if not isinstance(data, dict):
        raise ValueError("Front matter must be a YAML mapping (key: value).")

    return data, body


def files_under(roots: Iterable[Path]) -> List[Path]:
    """Return all Markdown files under the given roots (recursively)."""
    files: List[Path] = []
    for root in roots:
        if root.exists():
            files.extend(sorted(root.glob("**/*.md")))
    return files


def load_schema() -> Schema:
    """Load and compile schema settings from tools/schemas/requirement.schema.json."""
    raw = json.loads(Path("tools/schemas/requirement.schema.json").read_text(encoding="utf-8"))

    # Required top-level keys
    required = set(raw["required"])
    enum_levels = set(raw["enums"]["level"])
    enum_status = set(raw["enums"]["status"])
    allowed_link_keys = set(raw["link_keys"])

    # Optional settings with defaults
    id_patterns_raw = raw.get("id_patterns", {})
    testcase_pattern_raw = raw.get("testcase_pattern", r"^TC-\d+$")

    id_patterns = {level: re.compile(pattern) for level, pattern in id_patterns_raw.items()}
    testcase_pattern = re.compile(testcase_pattern_raw)

    # Recognize req->TRQ link aliases (e.g., covered_by) in addition to verified_by
    req_to_trq_aliases = {"verified_by"}
    if "covered_by" in allowed_link_keys:
        # Add 'covered_by' as an alias only if schema declares it
        req_to_trq_aliases.add("covered_by")

    return Schema(
        required=required,
        enum_levels=enum_levels,
        enum_status=enum_status,
        allowed_link_keys=allowed_link_keys,
        id_patterns=id_patterns,
        testcase_pattern=testcase_pattern,
        req_to_trq_aliases=req_to_trq_aliases,
    )


def normalize_links(links: object) -> List[Dict[str, object]]:
    """
    Accept links as a dict or list of dicts; return list[dict].
    Non-dict entries are ignored by the caller.
    """
    if isinstance(links, dict):
        return [links]
    if isinstance(links, list):
        return links
    return []


# --- Loading requirement & test case IDs --------------------------------------


def load_requirements() -> Tuple[Dict[str, Dict[str, object]], Dict[str, str]]:
    """
    Load all requirement files (including TRQ) and return:
      - reqs: id -> front_matter (plus internal _path/_body_len)
      - level_index: id -> level
    """
    reqs: Dict[str, Dict[str, object]] = {}
    level_index: Dict[str, str] = {}

    for path in files_under(REQ_ROOTS):
        text = path.read_text(encoding="utf-8")
        fm, body = read_front_matter(text)
        if fm is None:
            raise ValueError(f"Missing YAML front matter: {path}")

        rid = str(fm.get("id") or "").strip()
        lvl = str(fm.get("level") or "").strip()

        fm["_path"] = str(path)
        fm["_body_len"] = len(body)

        if not rid:
            raise ValueError(f"Missing 'id' in {path}")
        if rid in reqs:
            prev = reqs[rid]["_path"]
            raise ValueError(f"Duplicate id '{rid}' in {path} (already seen in {prev})")

        reqs[rid] = fm
        level_index[rid] = lvl

    return reqs, level_index


def load_testcase_ids(schema: Schema) -> Set[str]:
    """Return all test case IDs (TC-xxx) under verification/test-cases."""
    test_ids: Set[str] = set()
    for path in files_under(TC_ROOTS):
        text = path.read_text(encoding="utf-8")
        fm, _ = read_front_matter(text)
        if fm is None:
            print(f"[WARN] Missing YAML front matter in test case: {path}")
            continue
        tid = str(fm.get("id") or "").strip()
        if tid:
            if not schema.testcase_pattern.match(tid):
                print(
                    f"[WARN] Test case {tid}: does not match pattern {schema.testcase_pattern.pattern}"
                )
            test_ids.add(tid)
    return test_ids


# --- Field & enum checks ------------------------------------------------------


def validate_fields_and_enums(reqs: Dict[str, Dict[str, object]], schema: Schema) -> bool:
    """Validate required fields, enums, and ID patterns by level."""
    ok = True

    for rid, fm in reqs.items():
        lvl = str(fm.get("level") or "").strip()
        status = str(fm.get("status") or "").strip()
        title = str(fm.get("title") or "").strip()
        path = fm.get("_path")

        # Required fields
        for k in ("id", "title", "status", "level"):
            if not fm.get(k):
                ok = False
                print(f"[ERROR] {rid or '(no id)'}: missing '{k}' in {path}")

        # Enums
        if lvl and lvl not in schema.enum_levels:
            ok = False
            print(f"[ERROR] {rid}: invalid level '{lvl}' (allowed: {sorted(schema.enum_levels)})")
        if status and status not in schema.enum_status:
            ok = False
            print(
                f"[ERROR] {rid}: invalid status '{status}' (allowed: {sorted(schema.enum_status)})"
            )

        # ID pattern per level (if provided for this level)
        if lvl in schema.id_patterns:
            pattern = schema.id_patterns[lvl]
            if not pattern.match(rid):
                ok = False
                print(
                    f"[ERROR] {rid}: ID does not match pattern for level '{lvl}' ({pattern.pattern})"
                )

        # Basic title presence
        if not title:
            ok = False
            print(f"[ERROR] {rid}: empty 'title' in {path}")

    return ok


# --- Link validation (Model A) ------------------------------------------------


def validate_links_model_a(
    reqs: Dict[str, Dict[str, object]],
    level_index: Dict[str, str],
    test_ids: Set[str],
    schema: Schema,
) -> bool:
    """Validate links according to Model A semantics."""
    ok = True

    all_ids = set(reqs.keys())
    verification_ids = {i for i, l in level_index.items() if l == "verification"}
    non_verif_ids = all_ids - verification_ids  # BR/SR/TR

    for rid, fm in reqs.items():
        lvl = level_index.get(rid, "")
        links_list = normalize_links(fm.get("links", []))

        for link in links_list:
            if not isinstance(link, dict):
                ok = False
                print(f"[ERROR] {rid}: link must be a mapping (got {type(link).__name__})")
                continue

            for key, targets in link.items():
                if key not in schema.allowed_link_keys:
                    ok = False
                    print(
                        f"[ERROR] {rid}: invalid link type '{key}' (allowed: {sorted(schema.allowed_link_keys)})"
                    )
                    continue

                # Normalize scalar vs list
                target_list = targets if isinstance(targets, list) else [targets]

                # Free-form keys: no target enforcement
                if key in {"hazards", "rationale"}:
                    continue

                if lvl in {"business", "system", "software"}:
                    # Requirement -> TRQ via verified_by (and/or covered_by if declared)
                    if key in schema.req_to_trq_aliases:
                        for t in target_list:
                            if t not in verification_ids:
                                ok = False
                                print(
                                    f"[ERROR] {rid}: link '{key}' -> '{t}' must reference a verification requirement id (TRQ-xxx); not found."
                                )
                    # Requirement should not use verification-level keys
                    elif key in {"tested_by", "verifies"}:
                        ok = False
                        print(
                            f"[ERROR] {rid}: link '{key}' is invalid at requirement level; "
                            f"use '{'/'.join(sorted(schema.req_to_trq_aliases))}' to point to TRQ, and let TRQ use 'tested_by'/'verifies'."
                        )
                    # Hierarchy/dependency links (parent/derives/satisfies/depends_on) must resolve
                    elif key in {"parent", "derives", "satisfies", "depends_on"}:
                        for t in target_list:
                            if t not in all_ids:
                                ok = False
                                print(
                                    f"[ERROR] {rid}: link '{key}' -> '{t}' does not resolve to a known requirement id"
                                )

                elif lvl == "verification":
                    # TRQ -> Requirement via verifies (must point to BR/SR/TR)
                    if key == "verifies":
                        for t in target_list:
                            if t not in non_verif_ids:
                                ok = False
                                print(
                                    f"[ERROR] {rid}: link 'verifies' -> '{t}' must reference a business/system/software requirement id; not found."
                                )
                    # TRQ -> Test case via tested_by
                    elif key == "tested_by":
                        for t in target_list:
                            if t not in test_ids:
                                ok = False
                                print(
                                    f"[ERROR] {rid}: link 'tested_by' -> '{t}' must reference a test case id (TC-xxx); not found."
                                )
                    # TRQ should not use req->TRQ keys
                    elif key in schema.req_to_trq_aliases:
                        ok = False
                        print(
                            f"[ERROR] {rid}: link '{key}' is invalid at verification level; TRQ should use 'verifies' (-> BR/SR/TR) and 'tested_by' (-> TC-xxx)."
                        )
                    # Allow hierarchy/dependency links
                    elif key in {"parent", "derives", "satisfies", "depends_on"}:
                        for t in target_list:
                            if t not in all_ids:
                                ok = False
                                print(
                                    f"[ERROR] {rid}: link '{key}' -> '{t}' does not resolve to a known requirement id"
                                )
                else:
                    ok = False
                    print(f"[ERROR] {rid}: unknown or missing level '{lvl}'")

    return ok


# --- CLI ----------------------------------------------------------------------


def main() -> None:
    """Entry point for validator."""
    try:
        schema = load_schema()
        reqs, level_index = load_requirements()
        test_ids = load_testcase_ids(schema)
    except Exception as exc:
        print(f"[FAIL] Validator setup failed: {exc}", file=sys.stderr)
        sys.exit(1)

    ok_fields = validate_fields_and_enums(reqs, schema)
    ok_links = validate_links_model_a(reqs, level_index, test_ids, schema)

    if ok_fields and ok_links:
        print("[OK] Requirements validation passed.")
        sys.exit(0)
    else:
        print("[FAIL] Requirements validation failed.")
        sys.exit(1)


if __name__ == "__main__":
    main()

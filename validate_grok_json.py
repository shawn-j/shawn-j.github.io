#!/usr/bin/env python3
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

# --- CONFIG: expected shapes -------------------------------------

# Global / diagnostic reasoning pack shape (the big one you’ve been using)
GLOBAL_REQUIRED_KEYS = [
    "context_you_should_have_used",
    "thought_process_failures",
    "failure_patterns",
    "grok_strengths_and_limitations",
    "multi_llm_roles",
    "power_user_best_practices",
    "team_of_models_architecture",
    "reasoning_strategy_pack",
]

# Example minimal shape for a thread-specific JSON
# You can adjust this later if you formalize a schema.
THREAD_REQUIRED_KEYS = [
    "thread_name",           # string, e.g. "Kawaii dessert PMF – Grok role"
    "primary_goal",          # string
    "niche_or_topic",        # string
    "tasks_for_grok",        # list of strings
    "hard_constraints",      # list of strings
    "output_requirements",   # list of strings (e.g. "JSON only", "tables", etc.)
    "priority_rules",        # list of strings (e.g. "no made-up numbers")
]

def load_json(path: Path) -> Any:
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"[ERROR] {path}: invalid JSON syntax:\n  {e}", file=sys.stderr)
        sys.exit(1)


def detect_mode(obj: Dict[str, Any]) -> str:
    """
    Try to guess whether this is a GLOBAL pack or THREAD-specific pack
    based on its keys. If ambiguous, default to GLOBAL and just warn.
    """
    keys = set(obj.keys())
    has_global = any(k in keys for k in GLOBAL_REQUIRED_KEYS)
    has_thread = any(k in keys for k in THREAD_REQUIRED_KEYS)

    if has_global and not has_thread:
        return "global"
    if has_thread and not has_global:
        return "thread"
    if has_global and has_thread:
        # Rare case; treat as global and warn
        print("[WARN] JSON contains keys from both GLOBAL and THREAD schemas; "
              "treating as GLOBAL for validation.", file=sys.stderr)
        return "global"

    # Fallback: assume global to be conservative
    print("[WARN] Could not determine schema type; assuming GLOBAL.", file=sys.stderr)
    return "global"


def validate_list_field(obj: Dict[str, Any], key: str, errors: List[str]) -> None:
    if key not in obj:
        errors.append(f"Missing required key: {key}")
        return
    if not isinstance(obj[key], list):
        errors.append(f"Key '{key}' must be a list, found {type(obj[key]).__name__}")


def validate_string_field(obj: Dict[str, Any], key: str, errors: List[str]) -> None:
    if key not in obj:
        errors.append(f"Missing required key: {key}")
        return
    if not isinstance(obj[key], str):
        errors.append(f"Key '{key}' must be a string, found {type(obj[key]).__name__}")


def validate_global(obj: Dict[str, Any]) -> List[str]:
    errors: List[str] = []

    for key in GLOBAL_REQUIRED_KEYS:
        if key not in obj:
            errors.append(f"Missing required key: {key}")
        else:
            # These are all expected to be lists
            if not isinstance(obj[key], list):
                errors.append(
                    f"Key '{key}' must be a list (array), found {type(obj[key]).__name__}"
                )

    return errors


def validate_thread(obj: Dict[str, Any]) -> List[str]:
    errors: List[str] = []

    # required string fields
    for key in ["thread_name", "primary_goal", "niche_or_topic"]:
        validate_string_field(obj, key, errors)

    # required list fields
    for key in [
        "tasks_for_grok",
        "hard_constraints",
        "output_requirements",
        "priority_rules",
    ]:
        validate_list_field(obj, key, errors)

    return errors


def main():
    if len(sys.argv) != 2:
        print("Usage: validate_grok_json.py path/to/file.json", file=sys.stderr)
        sys.exit(1)

    path = Path(sys.argv[1])
    if not path.exists():
        print(f"[ERROR] File not found: {path}", file=sys.stderr)
        sys.exit(1)

    obj = load_json(path)

    if not isinstance(obj, dict):
        print(f"[ERROR] Root JSON must be an object, found {type(obj).__name__}", file=sys.stderr)
        sys.exit(1)

    mode = detect_mode(obj)

    if mode == "global":
        errors = validate_global(obj)
    else:
        errors = validate_thread(obj)

    if errors:
        print(f"[FAIL] {path} failed {mode.upper()} validation:")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)
    else:
        print(f"[OK] {path} is valid {mode.upper()} JSON.")


if __name__ == "__main__":
    main()

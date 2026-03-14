from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


@dataclass
class FilterSpec:
    key: str
    operator: str  # eq, contains, gte, lte, regex
    value: str


def parse_filter(raw: str) -> FilterSpec:
    """Parse a filter string like 'key:value', 'moves:>=50', 'name:~pattern'."""
    if ":" not in raw:
        raise ValueError(f"Invalid filter '{raw}': expected 'key:value' format")

    key, rest = raw.split(":", 1)
    key = key.strip()

    if rest.startswith(">="):
        return FilterSpec(key=key, operator="gte", value=rest[2:])
    elif rest.startswith("<="):
        return FilterSpec(key=key, operator="lte", value=rest[2:])
    elif rest.startswith("~"):
        return FilterSpec(key=key, operator="regex", value=rest[1:])
    elif rest.startswith("*") and rest.endswith("*"):
        return FilterSpec(key=key, operator="contains", value=rest[1:-1])
    else:
        return FilterSpec(key=key, operator="eq", value=rest)


def _get_nested(item: dict, key: str) -> Any:
    """Support dot-notation for nested keys like 'user.name'."""
    parts = key.split(".")
    val = item
    for part in parts:
        if not isinstance(val, dict):
            return None
        val = val.get(part)
    return val


def apply_filter(item: dict, spec: FilterSpec) -> bool:
    """Return True if item matches the filter spec."""
    val = _get_nested(item, spec.key)
    if val is None:
        return False

    str_val = str(val).lower()
    filter_val = spec.value.lower()

    match spec.operator:
        case "eq":
            return str_val == filter_val
        case "contains":
            return filter_val in str_val
        case "gte":
            try:
                return float(val) >= float(spec.value)
            except (TypeError, ValueError):
                return str_val >= filter_val
        case "lte":
            try:
                return float(val) <= float(spec.value)
            except (TypeError, ValueError):
                return str_val <= filter_val
        case "regex":
            return bool(re.search(spec.value, str(val), re.IGNORECASE))
        case _:
            return False


def apply_filters(item: dict, specs: list[FilterSpec]) -> bool:
    """Return True if item matches ALL filter specs (AND logic)."""
    return all(apply_filter(item, spec) for spec in specs)

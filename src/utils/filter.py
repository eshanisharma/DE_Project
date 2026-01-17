from __future__ import annotations

import re
from typing import Dict, Iterable, Iterator, List, Optional, Sequence
from urllib.parse import urlsplit, urlunsplit


def _collect_text_fields(data: Dict, keys: Optional[Sequence[str]] = None) -> str:
    """
    Pulls string values from a dict (all or selected keys) and joins them into one lowercase string for easy token checks.
    """
    parts: List[str] = []
    if keys:
        for key in keys:
            value = data.get(key)
            if isinstance(value, str):
                parts.append(value)
    else:
        for value in data.values():
            if isinstance(value, str):
                parts.append(value)
    return " ".join(parts).lower()


def _token_in_text(text: str, token: str) -> bool:
    """
    Check if a token is present in text, using word boundaries for short tokens.
    """
    if not token:
        return False
    token_cf = token.lower()
    # for matching "ny"
    if len(token_cf) <= 2:
        regex_match = re.search(rf"\b{re.escape(token_cf)}\b", text)
        if regex_match is not None:
            return True
        else:
            return False
    # for matching longer tokens like "new york" or "ppo"
    else:
        return token_cf in text


def reporting_plan_matches(
    plan: Dict,
    state_tokens: Iterable[str],
    network_tokens: Iterable[str],
) -> bool:
    """
    Uses the two helpers above to determine if a single plan contains both state and network tokens.
    """
    text = _collect_text_fields(plan)
    has_state = any(_token_in_text(text, token) for token in state_tokens)
    has_network = any(_token_in_text(text, token) for token in network_tokens)
    return has_state and has_network


def description_matches(
    entry: Dict,
    state_tokens: Iterable[str],
    network_tokens: Iterable[str],
) -> bool:
    entry_text = _collect_text_fields(entry, keys=("description",))
    has_state = any(_token_in_text(entry_text, token) for token in state_tokens)
    has_network = any(_token_in_text(entry_text, token) for token in network_tokens)
    return has_state and has_network


def extract_in_network_urls(reporting_structure: Dict) -> Iterator[str]:
    """
    Yield in-network file URLs from a reporting_structure item.
    """
    for entry in reporting_structure.get("in_network_files", []):
        location = entry.get("location")
        if isinstance(location, str) and location:
            yield location


def extract_matching_in_network_urls(
    reporting_structure: Dict,
    state_tokens: Optional[Iterable[str]] = None,
    network_tokens: Optional[Iterable[str]] = None,
    metrics: Optional[Dict[str, int]] = None,
) -> Iterator[str]:
    """
    Yield in-network URLs when the reporting plan matches state + network tokens.
    Falls back to description matching if plan fields are not informative.
    """
    state_tokens = ["new york", "newyork", "ny"]
    network_tokens = ["ppo"]

    plans = reporting_structure.get("reporting_plans", [])
    if metrics is not None:
        metrics["total_reporting_plans_parsed"] += len(plans)

    matched_plans = [
        plan
        for plan in plans
        if reporting_plan_matches(plan, state_tokens, network_tokens)
    ]
    if metrics is not None:
        metrics["ny_ppo_reporting_plans"] += len(matched_plans)

    if matched_plans:
        urls = list(extract_in_network_urls(reporting_structure))
        if metrics is not None:
            metrics["urls_from_plan_matches"] += len(urls)
        for url in urls:
            yield url
        return

    for entry in reporting_structure.get("in_network_files", []):
        if description_matches(entry, state_tokens, network_tokens):
            location = entry.get("location")
            if isinstance(location, str) and location:
                if metrics is not None:
                    metrics["urls_from_description_matches"] += 1
                yield location


def _normalize_url(url: str) -> str:
    """
    Normalize a URL by stripping query parameters and fragments.
    """
    parts = urlsplit(url)
    return urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))


def dedupe_urls(urls: Iterable[str]) -> Iterator[str]:
    """
    Yield URLs in first-seen order, skipping duplicates.
    """
    seen = set()
    for url in urls:
        normalized = _normalize_url(url)
        if normalized not in seen:
            seen.add(normalized)
            yield url

from __future__ import annotations

import os

from typing import Any

from config import ROOT_DIR


def _split_items(value: Any) -> list[str]:
    """
    Normalizes comma/newline separated values into a compact string list.

    Args:
        value (Any): Raw user-provided value

    Returns:
        items (list[str]): Cleaned list of strings
    """
    if value is None:
        return []

    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]

    if not isinstance(value, str):
        return [str(value).strip()] if str(value).strip() else []

    normalized = value.replace("\n", ",")
    return [item.strip() for item in normalized.split(",") if item.strip()]


def normalize_content_profile(content_profile: dict | None) -> dict:
    """
    Returns a normalized content profile used by service-led content prompts.

    Args:
        content_profile (dict | None): Raw profile data from the account cache

    Returns:
        profile (dict): Normalized profile
    """
    raw = content_profile or {}

    profile = {
        "content_mode": str(raw.get("content_mode", "") or "").strip().lower(),
        "content_variant": str(raw.get("content_variant", "") or "").strip().lower(),
        "target_customer": str(raw.get("target_customer", "") or "").strip(),
        "offer_name": str(raw.get("offer_name", "") or "").strip(),
        "primary_problem": str(raw.get("primary_problem", "") or "").strip(),
        "desired_outcome": str(raw.get("desired_outcome", "") or "").strip(),
        "cta_url": str(raw.get("cta_url", "") or "").strip(),
        "case_brief_file": str(raw.get("case_brief_file", "") or "").strip(),
        "review_notes": str(raw.get("review_notes", "") or "").strip(),
        "proof_points": _split_items(raw.get("proof_points")),
        "content_pillars": _split_items(raw.get("content_pillars")),
    }

    if not profile["content_mode"]:
        has_strategy_data = any(
            [
                profile["target_customer"],
                profile["offer_name"],
                profile["primary_problem"],
                profile["desired_outcome"],
                profile["cta_url"],
                profile["case_brief_file"],
                profile["review_notes"],
                profile["proof_points"],
                profile["content_pillars"],
            ]
        )
        profile["content_mode"] = "service_case_study" if has_strategy_data else "legacy"

    if not profile["content_variant"]:
        profile["content_variant"] = "general"

    return profile


def has_service_strategy(content_profile: dict | None) -> bool:
    """
    Determines whether an account should use the personalized service-led prompts.

    Args:
        content_profile (dict | None): Account content profile

    Returns:
        enabled (bool): True when service-led prompts should be used
    """
    profile = normalize_content_profile(content_profile)
    return profile["content_mode"] == "service_case_study"


def build_profile_context(content_profile: dict | None) -> str:
    """
    Serializes the normalized profile into prompt-friendly bullet points.

    Args:
        content_profile (dict | None): Account content profile

    Returns:
        context (str): Compact text block
    """
    profile = normalize_content_profile(content_profile)

    lines = []
    if profile["target_customer"]:
        lines.append(f"Target customer: {profile['target_customer']}")
    if profile["content_variant"]:
        lines.append(f"Content variant: {profile['content_variant']}")
    if profile["offer_name"]:
        lines.append(f"Offer: {profile['offer_name']}")
    if profile["primary_problem"]:
        lines.append(f"Primary problem solved: {profile['primary_problem']}")
    if profile["desired_outcome"]:
        lines.append(f"Desired customer outcome: {profile['desired_outcome']}")
    if profile["proof_points"]:
        lines.append("Proof points: " + "; ".join(profile["proof_points"]))
    if profile["content_pillars"]:
        lines.append("Content pillars: " + "; ".join(profile["content_pillars"]))
    if profile["cta_url"]:
        lines.append(f"CTA URL: {profile['cta_url']}")
    if profile["case_brief_file"]:
        lines.append(f"Case brief file: {profile['case_brief_file']}")
    if profile["review_notes"]:
        lines.append(f"Review notes: {profile['review_notes']}")

    return "\n".join(lines)


def resolve_case_brief_path(content_profile: dict | None) -> str:
    """
    Resolves an optional case brief file path relative to the repo root.

    Args:
        content_profile (dict | None): Account content profile

    Returns:
        path (str): Absolute case brief path or empty string
    """
    profile = normalize_content_profile(content_profile)
    raw_path = profile["case_brief_file"]

    if not raw_path:
        return ""

    if os.path.isabs(raw_path):
        return raw_path

    return os.path.join(ROOT_DIR, raw_path)


def load_case_brief(content_profile: dict | None) -> str:
    """
    Loads an optional reusable case brief from disk.

    Args:
        content_profile (dict | None): Account content profile

    Returns:
        brief (str): Case brief text or empty string
    """
    resolved = resolve_case_brief_path(content_profile)

    if not resolved or not os.path.exists(resolved):
        return ""

    with open(resolved, "r", errors="ignore") as handle:
        return handle.read().strip()

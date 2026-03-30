from __future__ import annotations

from typing import Any


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
        "target_customer": str(raw.get("target_customer", "") or "").strip(),
        "offer_name": str(raw.get("offer_name", "") or "").strip(),
        "primary_problem": str(raw.get("primary_problem", "") or "").strip(),
        "desired_outcome": str(raw.get("desired_outcome", "") or "").strip(),
        "cta_url": str(raw.get("cta_url", "") or "").strip(),
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
                profile["proof_points"],
                profile["content_pillars"],
            ]
        )
        profile["content_mode"] = "service_case_study" if has_strategy_data else "legacy"

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

    return "\n".join(lines)

import os
import json

from config import ROOT_DIR


def _get_default_analytics_path() -> str:
    return os.path.join(ROOT_DIR, ".mp", "analytics.json")


def _read_analytics(analytics_path: str | None = None) -> dict:
    path = analytics_path or _get_default_analytics_path()
    if not os.path.exists(path):
        return {"videos": [], "pending_costs": []}
    try:
        with open(path, "r") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        from status import warning

        warning(f"Failed to read analytics file ({path}): {e}")
        return {"videos": [], "pending_costs": []}
    if not isinstance(data, dict):
        return {"videos": [], "pending_costs": []}
    data.setdefault("videos", [])
    data.setdefault("pending_costs", [])
    return data


def _write_analytics(data: dict, analytics_path: str | None = None) -> None:
    path = analytics_path or _get_default_analytics_path()
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
    except (OSError, TypeError) as e:
        from status import error

        error(f"Failed to write analytics file ({path}): {e}")


def record_image_cost(
    video_id: str,
    model: str,
    analytics_path: str | None = None,
) -> None:
    """Record one Gemini API image generation call for a video.

    Called once per generate_image() invocation. Accumulates calls
    in pending_costs until the video is finalized via finalize_video().
    """
    data = _read_analytics(analytics_path)
    pending = data["pending_costs"]

    existing = next((c for c in pending if c["video_id"] == video_id), None)
    if existing:
        existing["gemini_api_calls"] += 1
    else:
        pending.append(
            {
                "video_id": video_id,
                "gemini_api_calls": 1,
                "gemini_model": model,
            }
        )

    _write_analytics(data, analytics_path)


def finalize_video(
    video_id: str,
    title: str,
    niche: str,
    upload_date: str,
    analytics_path: str | None = None,
) -> None:
    """Move pending cost data into a completed video entry."""
    data = _read_analytics(analytics_path)

    cost_entry = next(
        (c for c in data["pending_costs"] if c["video_id"] == video_id),
        None,
    )
    cost = {
        "gemini_api_calls": cost_entry["gemini_api_calls"] if cost_entry else 0,
        "gemini_model": cost_entry["gemini_model"] if cost_entry else "",
    }

    data["videos"].append(
        {
            "video_id": video_id,
            "title": title,
            "niche": niche,
            "upload_date": upload_date,
            "cost": cost,
            "metrics_history": [],
        }
    )

    if cost_entry:
        data["pending_costs"].remove(cost_entry)

    _write_analytics(data, analytics_path)


def get_video_cost(video_id: str, analytics_path: str | None = None) -> dict | None:
    """Get cost data for a specific video."""
    data = _read_analytics(analytics_path)
    for video in data["videos"]:
        if video["video_id"] == video_id:
            return video["cost"]
    return None


def get_all_costs(analytics_path: str | None = None) -> list[dict]:
    """Get cost summary for all videos: [{video_id, niche, gemini_api_calls, ...}]."""
    data = _read_analytics(analytics_path)
    return [
        {
            "video_id": v["video_id"],
            "title": v["title"],
            "niche": v["niche"],
            "upload_date": v["upload_date"],
            "gemini_api_calls": v["cost"]["gemini_api_calls"],
            "gemini_model": v["cost"]["gemini_model"],
        }
        for v in data["videos"]
    ]

import csv
import os
from datetime import datetime

from config import ROOT_DIR, get_gemini_cost_per_call
from cost_tracker import _read_analytics


def generate_niche_summary(
    cost_per_call: float | None = None,
    analytics_path: str | None = None,
) -> list[dict]:
    """Aggregate video data by niche.

    Returns a list of dicts, each with:
        niche, video_count, total_views, total_likes, total_comments,
        total_api_calls, total_cost, views_per_cost
    """
    if cost_per_call is None:
        cost_per_call = get_gemini_cost_per_call()

    data = _read_analytics(analytics_path)
    niches: dict[str, dict] = {}

    for video in data["videos"]:
        niche = video["niche"]
        if niche not in niches:
            niches[niche] = {
                "niche": niche,
                "video_count": 0,
                "total_views": 0,
                "total_likes": 0,
                "total_comments": 0,
                "total_api_calls": 0,
            }

        entry = niches[niche]
        entry["video_count"] += 1
        entry["total_api_calls"] += video["cost"]["gemini_api_calls"]

        # Use latest metrics snapshot if available
        if video["metrics_history"]:
            latest = video["metrics_history"][-1]
            entry["total_views"] += latest["views"]
            entry["total_likes"] += latest["likes"]
            entry["total_comments"] += latest["comments"]

    result = []
    for entry in niches.values():
        total_cost = entry["total_api_calls"] * cost_per_call
        views_per_cost = entry["total_views"] / total_cost if total_cost > 0 else 0
        result.append(
            {
                **entry,
                "total_cost": total_cost,
                "views_per_cost": views_per_cost,
            }
        )

    return sorted(result, key=lambda x: x["views_per_cost"], reverse=True)


def print_niche_summary(analytics_path: str | None = None) -> None:
    """Print a formatted niche summary table to the terminal."""
    from prettytable import PrettyTable

    summary = generate_niche_summary(analytics_path=analytics_path)

    if not summary:
        print("No analytics data found.")
        return

    table = PrettyTable()
    table.field_names = [
        "Niche",
        "Videos",
        "Views",
        "Likes",
        "Comments",
        "Cost",
        "Views/Cost",
    ]

    for row in summary:
        table.add_row(
            [
                row["niche"],
                row["video_count"],
                f"{row['total_views']:,}",
                f"{row['total_likes']:,}",
                f"{row['total_comments']:,}",
                f"${row['total_cost']:.3f}",
                f"{row['views_per_cost']:,.0f}",
            ]
        )

    print(table)


def export_csv(
    output_path: str | None = None,
    analytics_path: str | None = None,
) -> str:
    """Export per-video analytics data to CSV.

    Returns:
        path to the created CSV file.
    """
    if output_path is None:
        exports_dir = os.path.join(ROOT_DIR, "exports")
        os.makedirs(exports_dir, exist_ok=True)
        date_str = datetime.now().strftime("%Y-%m-%d")
        output_path = os.path.join(exports_dir, f"analytics_{date_str}.csv")

    data = _read_analytics(analytics_path)

    fieldnames = [
        "video_id",
        "title",
        "niche",
        "upload_date",
        "gemini_api_calls",
        "views",
        "likes",
        "comments",
        "fetched_at",
    ]

    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for video in data["videos"]:
            latest_metrics = (
                video["metrics_history"][-1] if video["metrics_history"] else {}
            )
            writer.writerow(
                {
                    "video_id": video["video_id"],
                    "title": video["title"],
                    "niche": video["niche"],
                    "upload_date": video["upload_date"],
                    "gemini_api_calls": video["cost"]["gemini_api_calls"],
                    "views": latest_metrics.get("views", ""),
                    "likes": latest_metrics.get("likes", ""),
                    "comments": latest_metrics.get("comments", ""),
                    "fetched_at": latest_metrics.get("fetched_at", ""),
                }
            )

    return output_path

import csv
import json
import os
import pytest
from report import generate_niche_summary, export_csv


@pytest.fixture
def multi_video_analytics(tmp_path):
    """Analytics with multiple niches for report testing."""
    path = tmp_path / "analytics.json"
    data = {
        "videos": [
            {
                "video_id": "v1",
                "title": "Pasta Recipe",
                "niche": "cooking",
                "upload_date": "2026-03-20 10:00:00",
                "cost": {
                    "gemini_api_calls": 5,
                    "gemini_model": "gemini-3.1-flash-image-preview",
                },
                "metrics_history": [
                    {
                        "views": 1000,
                        "likes": 50,
                        "comments": 5,
                        "fetched_at": "2026-03-25 10:00:00",
                    },
                ],
            },
            {
                "video_id": "v2",
                "title": "Salad Tips",
                "niche": "cooking",
                "upload_date": "2026-03-21 10:00:00",
                "cost": {
                    "gemini_api_calls": 4,
                    "gemini_model": "gemini-3.1-flash-image-preview",
                },
                "metrics_history": [
                    {
                        "views": 2000,
                        "likes": 80,
                        "comments": 10,
                        "fetched_at": "2026-03-25 10:00:00",
                    },
                ],
            },
            {
                "video_id": "v3",
                "title": "HIIT Workout",
                "niche": "fitness",
                "upload_date": "2026-03-22 10:00:00",
                "cost": {
                    "gemini_api_calls": 6,
                    "gemini_model": "gemini-3.1-flash-image-preview",
                },
                "metrics_history": [
                    {
                        "views": 500,
                        "likes": 20,
                        "comments": 2,
                        "fetched_at": "2026-03-25 10:00:00",
                    },
                ],
            },
        ],
        "pending_costs": [],
    }
    path.write_text(json.dumps(data))
    return str(path)


class TestNicheSummary:
    def test_aggregates_by_niche(self, multi_video_analytics):
        summary = generate_niche_summary(
            cost_per_call=0.005,
            analytics_path=multi_video_analytics,
        )
        assert len(summary) == 2

        cooking = next(s for s in summary if s["niche"] == "cooking")
        assert cooking["video_count"] == 2
        assert cooking["total_views"] == 3000
        assert cooking["total_likes"] == 130

        fitness = next(s for s in summary if s["niche"] == "fitness")
        assert fitness["video_count"] == 1
        assert fitness["total_views"] == 500

    def test_calculates_cost(self, multi_video_analytics):
        summary = generate_niche_summary(
            cost_per_call=0.01,
            analytics_path=multi_video_analytics,
        )
        cooking = next(s for s in summary if s["niche"] == "cooking")
        # 5 + 4 = 9 calls * $0.01 = $0.09
        assert cooking["total_cost"] == pytest.approx(0.09)

    def test_calculates_views_per_cost(self, multi_video_analytics):
        summary = generate_niche_summary(
            cost_per_call=0.01,
            analytics_path=multi_video_analytics,
        )
        cooking = next(s for s in summary if s["niche"] == "cooking")
        # 3000 views / $0.09 cost
        assert cooking["views_per_cost"] == pytest.approx(3000 / 0.09)


class TestCsvExport:
    def test_creates_csv_file(self, multi_video_analytics, tmp_path):
        out = str(tmp_path / "export.csv")
        export_csv(output_path=out, analytics_path=multi_video_analytics)
        assert os.path.exists(out)

    def test_csv_has_correct_rows(self, multi_video_analytics, tmp_path):
        out = str(tmp_path / "export.csv")
        export_csv(output_path=out, analytics_path=multi_video_analytics)
        with open(out) as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        assert len(rows) == 3
        assert rows[0]["video_id"] == "v1"
        assert rows[0]["niche"] == "cooking"
        assert rows[0]["views"] == "1000"

import json
from cost_tracker import record_image_cost, get_video_cost, get_all_costs


class TestRecordImageCost:
    def test_records_single_call(self, tmp_analytics_path):
        record_image_cost(
            video_id="vid1",
            model="gemini-3.1-flash-image-preview",
            analytics_path=tmp_analytics_path,
        )
        data = json.loads(open(tmp_analytics_path).read())
        costs = data["pending_costs"]
        assert len(costs) == 1
        assert costs[0]["video_id"] == "vid1"
        assert costs[0]["gemini_api_calls"] == 1

    def test_accumulates_multiple_calls(self, tmp_analytics_path):
        for _ in range(3):
            record_image_cost(
                video_id="vid1",
                model="gemini-3.1-flash-image-preview",
                analytics_path=tmp_analytics_path,
            )
        data = json.loads(open(tmp_analytics_path).read())
        pending = [c for c in data["pending_costs"] if c["video_id"] == "vid1"]
        assert len(pending) == 1
        assert pending[0]["gemini_api_calls"] == 3


class TestGetVideoCost:
    def test_returns_cost_for_known_video(self, analytics_with_data):
        cost = get_video_cost("test123", analytics_path=analytics_with_data)
        assert cost["gemini_api_calls"] == 5

    def test_returns_none_for_unknown_video(self, analytics_with_data):
        cost = get_video_cost("unknown", analytics_path=analytics_with_data)
        assert cost is None


class TestGetAllCosts:
    def test_returns_all_video_costs(self, analytics_with_data):
        costs = get_all_costs(analytics_path=analytics_with_data)
        assert len(costs) == 1
        assert costs[0]["video_id"] == "test123"

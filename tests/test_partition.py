"""
ESO Logs partitions rankings per game update and defaults to the newest one.
Both rankings queries must pin the configured partition, otherwise the day a
new update launches the scanner silently publishes the new update's logs under
the old update's pages (this happened for U51 under /u50/ in Sept-Oct 2026).
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.eso_build_o_rama.api_client import ESOLogsAPIClient
from src.eso_build_o_rama.main import ESOBuildORM


class _FakeResponse:
    status_code = 200

    def json(self):
        return {"data": {"worldData": {"encounter": {
            "fightRankings": {"rankings": []},
            "characterRankings": {"rankings": []},
        }}}}


class _RecordingGraphQLClient:
    def __init__(self):
        self.calls = []

    async def execute(self, query, variables=None, **kwargs):
        self.calls.append((query, variables or {}))
        return _FakeResponse()


def _client(partition):
    api = object.__new__(ESOLogsAPIClient)  # skip OAuth in __init__
    api.client = _RecordingGraphQLClient()
    api.partition = partition
    api.min_request_delay = 0
    api.max_retries = 1
    api.retry_delay = 0
    api.last_request_time = 0
    return api


class TestRankingsPartition:
    def test_both_rankings_queries_pin_the_configured_partition(self):
        api = _client(29)
        asyncio.run(api.get_top_logs(zone_id=1, encounter_id=5, limit=3))
        # fightRankings, then the characterRankings fallback because the fake returns no rankings
        assert len(api.client.calls) == 2, [q.split("{")[0].strip() for q, _ in api.client.calls]
        assert "fightRankings" in api.client.calls[0][0]
        assert "characterRankings" in api.client.calls[1][0]
        for query, variables in api.client.calls:
            assert "partition: $partition" in query
            assert variables["partition"] == 29

    def test_unconfigured_partition_is_sent_as_null(self):
        api = _client(None)
        asyncio.run(api.get_top_logs(zone_id=1, encounter_id=5, limit=3))
        assert len(api.client.calls) == 2
        for _, variables in api.client.calls:
            assert "partition" in variables and variables["partition"] is None


class TestPartitionConfig:
    CONFIG = {"updates": {"u50": {"path_prefix": "u50", "partition": 29}, "u51": {"path_prefix": "u51"}}}

    def test_configured_update(self):
        assert ESOBuildORM.partition_for(self.CONFIG, "u50") == 29

    def test_update_without_partition_or_unknown(self):
        assert ESOBuildORM.partition_for(self.CONFIG, "u51") is None
        assert ESOBuildORM.partition_for(self.CONFIG, "u99") is None
        assert ESOBuildORM.partition_for(self.CONFIG, None) is None

    def test_repo_config_pins_every_non_pending_update(self):
        import json
        cfg = json.load(open(os.path.join(os.path.dirname(__file__), '..', 'data', 'update_config.json')))
        for key, info in cfg["updates"].items():
            if info.get("status") in ("active", "archived"):
                assert isinstance(info.get("partition"), int), f"{key} has no ESO Logs partition"

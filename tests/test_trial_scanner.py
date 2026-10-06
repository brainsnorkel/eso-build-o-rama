"""
Regression tests for TrialScanner fight matching and role-fallback builds.

Covers two production bugs:
- Trash fights pass expected_encounter_name=None; the name check must
  short-circuit instead of evaluating None + " /" (broke all Trash Builds).
- Role-fallback builds must carry the fight window so mundus buff queries
  are accepted by the ESO Logs API.
"""
import asyncio
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.eso_build_o_rama.api_client import ESOLogsAPIClient
from src.eso_build_o_rama.models import PlayerBuild, TrialReport
from src.eso_build_o_rama.trial_scanner import TrialScanner


class TestFightNameMatches:
    """TrialScanner._fight_name_matches is the single source of truth for name validation."""

    def test_none_encounter_accepts_any_fight_name(self):
        # Trash fights skip validation; this must not raise.
        assert TrialScanner._fight_name_matches("Trash", None) is True
        assert TrialScanner._fight_name_matches("", None) is True
        assert TrialScanner._fight_name_matches(None, None) is True

    def test_exact_match(self):
        assert TrialScanner._fight_name_matches("The Mage", "The Mage") is True

    def test_composite_names(self):
        assert TrialScanner._fight_name_matches("Z'Maja / Shade of Z'Maja", "Z'Maja") is True
        assert TrialScanner._fight_name_matches("Shade of Z'Maja / Z'Maja", "Z'Maja") is True

    def test_mismatch(self):
        assert TrialScanner._fight_name_matches("Varlariel", "The Mage") is False
        assert TrialScanner._fight_name_matches("The Mage Trash", "The Mage") is False
        assert TrialScanner._fight_name_matches(None, "The Mage") is False


class TestFallbackBuildFightWindow:
    """Role-fallback builds are built from a TrialReport, which must carry the fight window."""

    def _player(self) -> PlayerBuild:
        return PlayerBuild(
            character_name="Dagen Moltenhammer",
            player_id=7,
            class_name="Dragonknight",
            role="tank",
            subclasses=["Earthen", "Soldier", "Draconic"],
            sets_equipped={"Pearlescent Ward": 5, "Saxhleel Champion": 5, "Nazaray": 2},
        )

    def test_fallback_build_carries_fight_window(self):
        scanner = TrialScanner(api_client=object())  # no network client needed
        report = TrialReport(
            trial_name="Aetherian Archive",
            boss_name="Foundation Stone Atronach",
            fight_id=12,
            fight_start_time=1_000_000,
            fight_end_time=1_250_000,
            report_code="abc123",
            update_version="u50",
        )

        build = scanner._create_fallback_build(self._player(), report)

        assert build is not None
        assert build.fight_id == 12
        assert build.fight_start_time == 1_000_000
        assert build.fight_end_time == 1_250_000
        assert build.report_code == "abc123"
        assert build.best_player.character_name == "Dagen Moltenhammer"

    def test_fallback_build_without_window_defaults_to_zero(self):
        scanner = TrialScanner(api_client=object())
        report = TrialReport(trial_name="Aetherian Archive", boss_name="The Mage", fight_id=3)

        build = scanner._create_fallback_build(self._player(), report)

        assert build is not None
        assert build.fight_start_time == 0
        assert build.fight_end_time == 0


class TestWindowMs:
    """Zero or missing bounds must be sent as absent so the API falls back to fightIDs."""

    @pytest.mark.parametrize("value", [None, 0, 0.0])
    def test_absent_values(self, value):
        assert ESOLogsAPIClient._window_ms(value) is None

    def test_present_values_become_int_ms(self):
        assert ESOLogsAPIClient._window_ms(1234.9) == 1234
        assert ESOLogsAPIClient._window_ms(5) == 5


class _RecordingAPIClient:
    """Stub API client: records table queries and returns nothing, so
    _process_single_fight stops right after the name validation passes."""

    def __init__(self):
        self.calls = []

    async def get_report_table(self, **kwargs):
        self.calls.append(kwargs)
        return None


class TestProcessSingleFightNameValidation:
    """End-to-end check of the validation inside _process_single_fight."""

    REPORT = {
        "fights": [
            {"id": 7, "name": "Firstmage Overcharger", "startTime": 1000, "endTime": 82500},
            {"id": 12, "name": "The Mage", "startTime": 90000, "endTime": 250000},
        ]
    }

    def _run(self, fight_id, expected_encounter_name):
        client = _RecordingAPIClient()
        scanner = TrialScanner(api_client=client)
        result = asyncio.run(scanner._process_single_fight(
            self.REPORT, "abc123", fight_id, "Aetherian Archive", expected_encounter_name
        ))
        return result, client

    def test_trash_fight_with_no_expected_name_reaches_the_api(self):
        # Pre-fix this raised TypeError (None + " /") before any query was made.
        result, client = self._run(7, None)
        assert result is None  # stub returns no data, so no report is built
        assert len(client.calls) >= 1
        assert client.calls[0]["report_code"] == "abc123"

    def test_matching_boss_name_reaches_the_api(self):
        _, client = self._run(12, "The Mage")
        assert len(client.calls) >= 1

    def test_mismatched_boss_name_is_skipped_without_api_calls(self):
        result, client = self._run(7, "The Mage")
        assert result is None
        assert client.calls == []

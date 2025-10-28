#!/usr/bin/env python3
"""
Test different metrics for fightRankings query.

Compares 'speed' metric (current) vs 'points' metric (alternative)
to see if different metrics return different results.
"""

import asyncio
import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.eso_build_o_rama.api_client import ESOLogsAPIClient


async def test_metric(client, encounter_id: int, metric: str, trial_name: str):
    """
    Test a specific metric for fightRankings.

    Args:
        client: ESOLogsAPIClient instance
        encounter_id: Encounter ID to query
        metric: Metric type ('speed' or 'points')
        trial_name: Trial name for display
    """
    print(f"\n{'='*70}")
    print(f"Testing metric: {metric.upper()}")
    print(f"Trial: {trial_name}, Encounter ID: {encounter_id}")
    print(f"{'='*70}")

    query = f'''
    query GetRankings($encounterID: Int!) {{
      worldData {{
        encounter(id: $encounterID) {{
          fightRankings(
            metric: {metric}
          )
        }}
      }}
    }}
    '''

    try:
        result = await client._retry_on_rate_limit(
            client.client.execute,
            query=query,
            variables={"encounterID": encounter_id}
        )

        if result.status_code != 200:
            print(f"❌ API request failed with status {result.status_code}")
            return None

        data = result.json()

        if 'errors' in data:
            print(f"❌ GraphQL errors: {data['errors']}")
            return None

        fight_rankings = data['data']['worldData']['encounter']['fightRankings']

        # Extract rankings
        if isinstance(fight_rankings, dict):
            rankings = fight_rankings.get('rankings', [])
        elif isinstance(fight_rankings, list):
            rankings = fight_rankings
        else:
            print(f"❌ Unexpected fightRankings format: {type(fight_rankings)}")
            return None

        print(f"✅ Found {len(rankings)} rankings")

        if rankings:
            print(f"\nTop 5 Rankings:")
            for i, ranking in enumerate(rankings[:5], 1):
                report = ranking.get('report', {})
                code = report.get('code', 'N/A')
                duration = ranking.get('duration', 0)
                score = ranking.get('score', 0)
                guild = ranking.get('guild', {}).get('name', 'Unknown')

                print(f"  {i}. Report: {code}")
                print(f"     Duration: {duration/1000:.1f}s, Score: {score:.2f}")
                print(f"     Guild: {guild}")
        else:
            print("  ⚠️  No rankings data available")

        return rankings

    except Exception as e:
        print(f"❌ Error: {e}")
        return None


async def compare_metrics():
    """Compare speed vs points metrics for multiple trials."""
    client = ESOLogsAPIClient()

    try:
        print("="*70)
        print("FIGHTrankings METRIC COMPARISON TEST")
        print("="*70)

        # Test trials with expected data vs without
        test_cases = [
            # (encounter_id, trial_name, expected_data)
            (60, "Lucent Citadel - Xoryn", False),           # Known to have no data
            (57, "Sanity's Edge - Exarchanic Yaseyla", True), # Should have data
            (45, "Dreadsail Reef - Tideborn Taleria", True),  # Should have data
        ]

        for encounter_id, trial_name, expected_data in test_cases:
            print(f"\n\n{'#'*70}")
            print(f"TRIAL: {trial_name}")
            print(f"Expected Data: {'Yes' if expected_data else 'No'}")
            print(f"{'#'*70}")

            # Test speed metric
            speed_rankings = await test_metric(client, encounter_id, "speed", trial_name)

            # Test points metric
            points_rankings = await test_metric(client, encounter_id, "points", trial_name)

            # Compare results
            print(f"\n{'─'*70}")
            print(f"COMPARISON SUMMARY")
            print(f"{'─'*70}")
            print(f"Speed metric:  {len(speed_rankings) if speed_rankings else 0} rankings")
            print(f"Points metric: {len(points_rankings) if points_rankings else 0} rankings")

            if speed_rankings and points_rankings:
                if len(speed_rankings) == len(points_rankings):
                    print(f"✅ Same number of rankings")
                else:
                    print(f"⚠️  Different number of rankings!")
            elif not speed_rankings and not points_rankings:
                print(f"⚠️  No data for either metric")
            elif speed_rankings and not points_rankings:
                print(f"✅ Speed has data, points does not")
            elif points_rankings and not speed_rankings:
                print(f"✅ Points has data, speed does not")

        print("\n" + "="*70)
        print("TEST COMPLETE")
        print("="*70)

    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(compare_metrics())

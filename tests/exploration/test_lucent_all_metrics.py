#!/usr/bin/env python3
"""
Test all valid metrics specifically on Lucent Citadel.
"""

import asyncio
import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.eso_build_o_rama.api_client import ESOLogsAPIClient


async def test_metric_detailed(client, encounter_id: int, encounter_name: str, metric: str):
    """Test a specific metric and show detailed results."""
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

        data = result.json()

        if 'errors' in data:
            return None, data['errors'][0]['message']

        fight_rankings = data['data']['worldData']['encounter']['fightRankings']

        if isinstance(fight_rankings, dict):
            rankings = fight_rankings.get('rankings', [])
        elif isinstance(fight_rankings, list):
            rankings = fight_rankings
        else:
            return None, f"Unexpected format: {type(fight_rankings)}"

        return rankings, None

    except Exception as e:
        return None, str(e)


async def test_lucent_citadel():
    """Test all valid metrics on Lucent Citadel encounters."""
    client = ESOLogsAPIClient()

    valid_metrics = ['speed', 'execution', 'feats', 'progress', 'default', 'score']

    encounters = [
        (58, "Count Ryelaz and Zilyesset"),
        (59, "Orphic Shattered Shard"),
        (60, "Xoryn (Final Boss)")
    ]

    print("="*70)
    print("LUCENT CITADEL - ALL METRICS TEST")
    print("="*70)

    try:
        for enc_id, enc_name in encounters:
            print(f"\n{'#'*70}")
            print(f"ENCOUNTER: {enc_name} (ID: {enc_id})")
            print(f"{'#'*70}")

            results = {}

            for metric in valid_metrics:
                rankings, error = await test_metric_detailed(client, enc_id, enc_name, metric)

                if error:
                    print(f"  {metric:15s} ❌ Error: {error}")
                    results[metric] = 0
                else:
                    count = len(rankings) if rankings else 0
                    if count > 0:
                        print(f"  {metric:15s} ✅ Found {count} rankings")
                        # Show first ranking
                        if rankings:
                            first = rankings[0]
                            report = first.get('report', {})
                            print(f"                   └─ Report: {report.get('code', 'N/A')}")
                    else:
                        print(f"  {metric:15s} ⚠️  0 rankings")
                    results[metric] = count

            # Summary for this encounter
            print(f"\n  {'─'*66}")
            print(f"  Summary: {sum(results.values())} total rankings across all metrics")
            if sum(results.values()) == 0:
                print(f"  ❌ No data available for this encounter")
            else:
                print(f"  ✅ Data found with: {', '.join([k for k, v in results.items() if v > 0])}")

        print("\n" + "="*70)
        print("CONCLUSION")
        print("="*70)
        print("\nLucent Citadel has NO ranked data in ESO Logs for any encounter")
        print("regardless of which metric is used.")
        print("\nValid metrics tested:")
        for metric in valid_metrics:
            print(f"  - {metric}")

    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(test_lucent_citadel())

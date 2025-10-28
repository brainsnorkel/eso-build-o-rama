#!/usr/bin/env python3
"""
Test all possible metrics for fightRankings to find valid options.
"""

import asyncio
import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.eso_build_o_rama.api_client import ESOLogsAPIClient


async def test_metric(client, encounter_id: int, metric: str):
    """Test if a metric is valid."""
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
            error_msg = data['errors'][0]['message']
            return False, error_msg

        fight_rankings = data['data']['worldData']['encounter']['fightRankings']
        if isinstance(fight_rankings, dict):
            rankings = fight_rankings.get('rankings', [])
        else:
            rankings = fight_rankings if isinstance(fight_rankings, list) else []

        return True, len(rankings)

    except Exception as e:
        return False, str(e)


async def discover_metrics():
    """Try various metrics to find valid ones."""
    client = ESOLogsAPIClient()

    # Use Dreadsail Reef Tideborn Taleria (known to have data)
    encounter_id = 45

    # Possible metrics to test
    test_metrics = [
        'speed',      # Current
        'points',     # Tried
        'dps',        # Damage
        'hps',        # Healing
        'execution',  # Execution score
        'feats',      # Feats
        'progress',   # Progress
        'default',    # Default
        'rdps',       # Raid DPS
        'ndps',       # Normalized DPS
        'playerscore', # Player score
        'score',      # Generic score
    ]

    print("="*70)
    print("TESTING AVAILABLE METRICS FOR fightRankings")
    print("="*70)
    print(f"Test Encounter: Dreadsail Reef - Tideborn Taleria (ID: {encounter_id})")
    print("="*70)

    valid_metrics = []
    invalid_metrics = []

    try:
        for metric in test_metrics:
            print(f"\nTesting: {metric:15s} ", end='', flush=True)
            valid, result = await test_metric(client, encounter_id, metric)

            if valid:
                print(f"✅ VALID - Found {result} rankings")
                valid_metrics.append((metric, result))
            else:
                print(f"❌ INVALID - {result}")
                invalid_metrics.append((metric, result))

        print("\n" + "="*70)
        print("SUMMARY")
        print("="*70)

        print(f"\n✅ Valid Metrics ({len(valid_metrics)}):")
        for metric, count in valid_metrics:
            print(f"   - {metric:15s} ({count} rankings)")

        print(f"\n❌ Invalid Metrics ({len(invalid_metrics)}):")
        for metric, error in invalid_metrics:
            # Extract just the key error message
            if "does not exist" in error:
                print(f"   - {metric:15s} (not in enum)")
            else:
                print(f"   - {metric:15s} ({error[:50]}...)")

        print("\n" + "="*70)
        print("RECOMMENDATION")
        print("="*70)
        if valid_metrics:
            best = max(valid_metrics, key=lambda x: x[1])
            print(f"\nBest metric: '{best[0]}' with {best[1]} rankings")
            print(f"\nCurrent metric 'speed' returned: {dict(valid_metrics).get('speed', 'N/A')} rankings")

    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(discover_metrics())

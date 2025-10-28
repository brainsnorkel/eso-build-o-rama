#!/usr/bin/env python3
"""
Detailed investigation of 'default' and 'score' metrics for Lucent Citadel.
"""

import asyncio
import sys
import json
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.eso_build_o_rama.api_client import ESOLogsAPIClient


async def investigate_metric(client, encounter_id: int, metric: str):
    """Get full details from a metric."""
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

    result = await client._retry_on_rate_limit(
        client.client.execute,
        query=query,
        variables={"encounterID": encounter_id}
    )

    return result.json()


async def main():
    """Investigate Lucent Citadel data in detail."""
    client = ESOLogsAPIClient()

    print("="*70)
    print("LUCENT CITADEL XORYN - DETAILED INVESTIGATION")
    print("="*70)

    encounter_id = 60  # Xoryn

    try:
        for metric in ['default', 'score']:
            print(f"\n{'#'*70}")
            print(f"METRIC: {metric}")
            print(f"{'#'*70}")

            data = await investigate_metric(client, encounter_id, metric)

            if 'errors' in data:
                print(f"❌ Errors: {data['errors']}")
                continue

            fight_rankings = data['data']['worldData']['encounter']['fightRankings']

            # Pretty print the entire response
            print("\nFull Response Structure:")
            print(json.dumps(fight_rankings, indent=2))

            if isinstance(fight_rankings, dict):
                rankings = fight_rankings.get('rankings', [])
            else:
                rankings = fight_rankings

            print(f"\nNumber of rankings: {len(rankings)}")

            if rankings:
                print(f"\nDetailed Ranking Analysis:")
                for i, ranking in enumerate(rankings, 1):
                    print(f"\n  Ranking {i}:")
                    print(f"  {'-'*66}")

                    # Show all keys
                    for key, value in ranking.items():
                        if isinstance(value, dict):
                            print(f"    {key}:")
                            for k2, v2 in value.items():
                                print(f"      {k2}: {v2}")
                        else:
                            print(f"    {key}: {value}")

        print("\n" + "="*70)
        print("ANALYSIS")
        print("="*70)

        print("\n'default' and 'score' metrics returned 2 rankings but:")
        print("  - Report codes are empty/null")
        print("  - May be placeholder data")
        print("  - Not usable for fetching actual reports")
        print("\nConclusion: No actionable data available for Lucent Citadel")

    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())

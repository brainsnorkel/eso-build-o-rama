#!/usr/bin/env python3
"""Test Lucent Citadel API availability."""

import asyncio
import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.eso_build_o_rama.api_client import ESOLogsAPIClient


async def test_lucent_citadel():
    """Test if Lucent Citadel data is available."""
    client = ESOLogsAPIClient()

    try:
        # Get zone data
        print("Fetching zone data...")
        zones = await client.get_zones()

        # Find Lucent Citadel
        lucent = None
        for zone in zones:
            if zone.get('name') == 'Lucent Citadel':
                lucent = zone
                break

        if not lucent:
            print("❌ Lucent Citadel not found in zones")
            return

        print(f"✅ Found Lucent Citadel: {lucent}")
        zone_id = lucent['id']

        # Get encounters
        encounters = lucent.get('encounters', [])
        print(f"\nEncounters ({len(encounters)}):")
        for enc in encounters:
            print(f"  - {enc.get('name')} (ID: {enc.get('id')})")

        if not encounters:
            print("❌ No encounters found")
            return

        # Check final boss
        final_boss = encounters[-1]
        print(f"\nChecking final boss: {final_boss.get('name')} (ID: {final_boss.get('id')})")

        # Try to get rankings with different leaderboard types
        leaderboard_types = ['LogsOnly', 'All', 'Rankings']

        for lb_type in leaderboard_types:
            print(f"\nTrying leaderboard type: {lb_type}")
            try:
                rankings = await client.get_rankings(
                    zone_id=zone_id,
                    encounter_id=final_boss.get('id'),
                    limit=5
                )
                print(f"  ✅ Found {len(rankings) if rankings else 0} rankings")
                if rankings:
                    for i, rank in enumerate(rankings[:3], 1):
                        print(f"    {i}. Report: {rank.get('reportCode')} - {rank.get('reportFightID')}")
                    break
            except Exception as e:
                print(f"  ❌ Error: {e}")

    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(test_lucent_citadel())

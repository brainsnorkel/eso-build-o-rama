#!/usr/bin/env python3
"""
Compare fightRankings vs characterRankings (player rankings).

fightRankings = Team/group rankings (fastest clears)
characterRankings = Individual player rankings (highest DPS/HPS/etc)
"""

import asyncio
import sys
import json
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.eso_build_o_rama.api_client import ESOLogsAPIClient


async def test_fight_rankings(client, encounter_id: int, trial_name: str):
    """Test fightRankings (current implementation)."""
    query = '''
    query GetFightRankings($encounterID: Int!) {
      worldData {
        encounter(id: $encounterID) {
          fightRankings(
            metric: speed
          )
        }
      }
    }
    '''

    result = await client._retry_on_rate_limit(
        client.client.execute,
        query=query,
        variables={"encounterID": encounter_id}
    )

    data = result.json()

    if 'errors' in data:
        return None, data['errors']

    fight_rankings = data['data']['worldData']['encounter']['fightRankings']
    rankings = fight_rankings.get('rankings', []) if isinstance(fight_rankings, dict) else fight_rankings

    return rankings, None


async def test_character_rankings(client, encounter_id: int, trial_name: str, metric: str = "dps"):
    """Test characterRankings (player-based rankings)."""
    query = '''
    query GetCharacterRankings($encounterID: Int!, $metric: CharacterRankingMetricType!) {
      worldData {
        encounter(id: $encounterID) {
          characterRankings(
            metric: $metric
          )
        }
      }
    }
    '''

    result = await client._retry_on_rate_limit(
        client.client.execute,
        query=query,
        variables={
            "encounterID": encounter_id,
            "metric": metric
        }
    )

    data = result.json()

    if 'errors' in data:
        return None, data['errors']

    char_rankings = data['data']['worldData']['encounter']['characterRankings']
    rankings = char_rankings.get('rankings', []) if isinstance(char_rankings, dict) else char_rankings

    return rankings, None


async def compare_ranking_types():
    """Compare fightRankings vs characterRankings."""
    client = ESOLogsAPIClient()

    test_cases = [
        (60, "Lucent Citadel - Xoryn"),
        (45, "Dreadsail Reef - Tideborn Taleria"),
        (57, "Sanity's Edge - Exarchanic Yaseyla"),
    ]

    print("="*70)
    print("FIGHT RANKINGS vs CHARACTER RANKINGS COMPARISON")
    print("="*70)

    try:
        for encounter_id, trial_name in test_cases:
            print(f"\n{'#'*70}")
            print(f"TRIAL: {trial_name} (Encounter ID: {encounter_id})")
            print(f"{'#'*70}")

            # Test fightRankings (team/speed based)
            print(f"\n1. FIGHT RANKINGS (Team - Speed Metric)")
            print(f"{'─'*70}")
            fight_ranks, fight_error = await test_fight_rankings(client, encounter_id, trial_name)

            if fight_error:
                print(f"   ❌ Error: {fight_error}")
                fight_count = 0
            else:
                fight_count = len(fight_ranks) if fight_ranks else 0
                print(f"   ✅ Found {fight_count} team rankings")

                if fight_count > 0:
                    print(f"\n   Top 3 Teams:")
                    for i, rank in enumerate(fight_ranks[:3], 1):
                        report = rank.get('report', {})
                        guild = rank.get('guild', {}).get('name', 'Unknown')
                        duration = rank.get('duration', 0) / 1000
                        score = rank.get('score', 0)
                        code = report.get('code', 'N/A')

                        print(f"     {i}. Guild: {guild}")
                        print(f"        Duration: {duration:.1f}s, Score: {score:.0f}")
                        print(f"        Report: {code}")

            # Test characterRankings (individual player DPS)
            print(f"\n2. CHARACTER RANKINGS (Individual - DPS Metric)")
            print(f"{'─'*70}")
            char_ranks, char_error = await test_character_rankings(client, encounter_id, trial_name, "dps")

            if char_error:
                print(f"   ❌ Error: {char_error}")
                char_count = 0
            else:
                char_count = len(char_ranks) if char_ranks else 0
                print(f"   ✅ Found {char_count} player rankings")

                if char_count > 0:
                    print(f"\n   Top 5 Players:")
                    for i, rank in enumerate(char_ranks[:5], 1):
                        name = rank.get('name', 'Unknown')
                        class_name = rank.get('class', 'Unknown')
                        spec = rank.get('spec', 'Unknown')
                        amount = rank.get('amount', 0)
                        report = rank.get('report', {})
                        code = report.get('code', 'N/A')

                        print(f"     {i}. {name} ({class_name} - {spec})")
                        print(f"        DPS: {amount:,.0f}")
                        print(f"        Report: {code}")

            # Comparison
            print(f"\n{'─'*70}")
            print(f"COMPARISON SUMMARY")
            print(f"{'─'*70}")
            print(f"Fight Rankings (Teams):      {fight_count:3d} results")
            print(f"Character Rankings (Players): {char_count:3d} results")

            if fight_count == 0 and char_count == 0:
                print(f"❌ No data available with either method")
            elif fight_count > 0 and char_count == 0:
                print(f"⚠️  Team data exists, but no individual player data")
            elif fight_count == 0 and char_count > 0:
                print(f"✅ Individual player data exists!")
                print(f"   → characterRankings returns MORE data than fightRankings")
            else:
                print(f"✅ Both methods return data")

        print("\n" + "="*70)
        print("KEY DIFFERENCES")
        print("="*70)
        print("\nfightRankings (Current):")
        print("  • Returns TEAM/GROUP rankings (one per report)")
        print("  • Based on speed/execution/score metrics")
        print("  • Gives report codes to fetch full team data")
        print("  • Shows fastest clears, best teams")
        print("\ncharacterRankings (Alternative):")
        print("  • Returns INDIVIDUAL PLAYER rankings")
        print("  • Based on dps/hps/bossdps/tankhps metrics")
        print("  • Shows top performers across ALL reports")
        print("  • May include more reports than fightRankings")
        print("  • Each player = one ranking entry")

    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(compare_ranking_types())

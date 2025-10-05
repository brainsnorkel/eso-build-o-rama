#!/usr/bin/env python3
"""
Test script to find the correct way to get top-ranked reports from ESO Logs API.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.eso_build_o_rama.api_client import ESOLogsAPIClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def test_graphql_rankings():
    """Test using direct GraphQL query for character rankings."""
    
    client = ESOLogsAPIClient()
    
    print('='*70)
    print('Testing GraphQL Character Rankings Query')
    print('='*70)
    
    # GraphQL query for character rankings
    query = """
    query GetTopRankings($zoneID: Int!, $encounterID: Int, $metric: CharacterRankingMetricType) {
      worldData {
        encounter(id: $encounterID) {
          characterRankings(
            zoneID: $zoneID
            metric: $metric
          ) {
            rankings(limit: 20) {
              name
              class
              spec
              amount
              report {
                code
                startTime
                fightID
              }
            }
          }
        }
      }
    }
    """
    
    # Get encounters for Aetherian Archive
    zones = await client.get_zones()
    aa_zone = [z for z in zones if z['id'] == 1][0]
    
    if not aa_zone['encounters']:
        print('No encounters found')
        await client.close()
        return
    
    # Use The Mage (final boss) for rankings
    mage_encounter = aa_zone['encounters'][-1]
    print(f'\nUsing encounter: {mage_encounter["name"]} (ID: {mage_encounter["id"]})')
    
    variables = {
        "zoneID": 1,
        "encounterID": mage_encounter['id'],
        "metric": "dps"
    }
    
    try:
        # Execute the GraphQL query
        result = await client.client.execute(query, variables)
        
        print(f'\nResult type: {type(result)}')
        
        # Navigate the response
        if hasattr(result, 'world_data') and result.world_data:
            world_data = result.world_data
            if hasattr(world_data, 'encounter') and world_data.encounter:
                encounter_data = world_data.encounter
                if hasattr(encounter_data, 'character_rankings') and encounter_data.character_rankings:
                    char_rankings = encounter_data.character_rankings
                    if hasattr(char_rankings, 'rankings') and char_rankings.rankings:
                        rankings = char_rankings.rankings
                        
                        print(f'\nFound {len(rankings)} rankings')
                        
                        # Extract unique report codes
                        report_codes = {}
                        for ranking in rankings:
                            report_code = ranking.report.code
                            if report_code not in report_codes:
                                report_codes[report_code] = {
                                    'code': report_code,
                                    'characters': [],
                                    'top_dps': ranking.amount
                                }
                            report_codes[report_code]['characters'].append({
                                'name': ranking.name,
                                'class': ranking.class_,
                                'dps': ranking.amount
                            })
                        
                        print(f'\n{"="*70}')
                        print(f'Top 5 HIGHEST RANKED Reports (by character DPS):')
                        print(f'{"="*70}')
                        
                        # Sort by top DPS
                        sorted_reports = sorted(report_codes.values(), key=lambda x: x['top_dps'], reverse=True)
                        
                        for i, report_info in enumerate(sorted_reports[:5], 1):
                            print(f'\n{i}. Report Code: {report_info["code"]}')
                            print(f'   Top DPS: {report_info["top_dps"]:,}')
                            print(f'   Characters in top 20: {len(report_info["characters"])}')
                            print(f'   URL: https://www.esologs.com/reports/{report_info["code"]}')
                            print(f'   Top character: {report_info["characters"][0]["name"]} ({report_info["characters"][0]["class"]})')
        
    except Exception as e:
        print(f'Error: {e}')
        import traceback
        traceback.print_exc()
    
    await client.close()


if __name__ == "__main__":
    asyncio.run(test_graphql_rankings())

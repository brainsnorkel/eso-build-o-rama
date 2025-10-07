#!/usr/bin/env python3
"""
Query Testing Utility
Test different GraphQL queries against ESO Logs API to see what reports are returned.
"""

import asyncio
import json
import sys
import os
from pathlib import Path
from typing import Dict, Any, Optional

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.eso_build_o_rama.api_client import ESOLogsAPIClient
from dotenv import load_dotenv

load_dotenv()


class QueryTester:
    """Test different query variations and display results."""
    
    def __init__(self):
        """Initialize the API client."""
        self.client = ESOLogsAPIClient(min_request_delay=1.0)
    
    async def test_query(
        self,
        query_type: str,
        encounter_id: int,
        metric: str = "dps",
        leaderboard: Optional[str] = None,
        limit: int = 5
    ) -> Dict[str, Any]:
        """
        Test a specific query configuration.
        
        Args:
            query_type: Type of rankings (characterRankings, fightRankings, etc.)
            encounter_id: Encounter ID to query
            metric: Metric type (dps, hps, playerscore, etc.)
            leaderboard: Optional leaderboard type (LogsOnly, etc.)
            limit: Number of results to return
            
        Returns:
            Query results
        """
        # Build the query dynamically
        leaderboard_param = f'leaderboard: {leaderboard}' if leaderboard else ''
        
        query = f'''
        query GetRankings($encounterID: Int!) {{
          worldData {{
            encounter(id: $encounterID) {{
              {query_type}(
                metric: {metric}
                {leaderboard_param}
              )
            }}
          }}
        }}
        '''
        
        print(f"\n{'='*80}")
        print(f"Testing: {query_type} | metric: {metric} | leaderboard: {leaderboard}")
        print(f"{'='*80}")
        print(f"\nQuery:\n{query}")
        print(f"\nVariables: {{'encounterID': {encounter_id}}}\n")
        
        try:
            result = await self.client.client.execute(
                query=query,
                variables={"encounterID": encounter_id}
            )
            
            if result.status_code != 200:
                print(f"❌ Request failed with status {result.status_code}")
                return {"error": f"HTTP {result.status_code}"}
            
            data = result.json()
            
            if 'errors' in data:
                print(f"❌ GraphQL Errors:")
                for error in data['errors']:
                    print(f"   - {error.get('message', 'Unknown error')}")
                    if 'locations' in error:
                        print(f"     Location: {error['locations']}")
                return {"error": data['errors']}
            
            # Extract the rankings data
            rankings_data = data['data']['worldData']['encounter'][query_type]
            
            # Display results
            self._display_results(rankings_data, query_type, limit)
            
            return rankings_data
            
        except Exception as e:
            print(f"❌ Exception: {e}")
            return {"error": str(e)}
    
    def _display_results(self, rankings_data: Any, query_type: str, limit: int):
        """Display the rankings results in a readable format."""
        print(f"\n✅ Query Successful!")
        print(f"\nData Type: {type(rankings_data)}")
        
        # Handle different response formats
        if isinstance(rankings_data, dict):
            print(f"\nResponse has keys: {list(rankings_data.keys())}")
            rankings = rankings_data.get('rankings', rankings_data.get('data', []))
        elif isinstance(rankings_data, list):
            rankings = rankings_data
        else:
            print(f"\n⚠️  Unexpected data format")
            print(json.dumps(rankings_data, indent=2)[:500])
            return
        
        if not rankings:
            print("\n⚠️  No rankings returned")
            return
        
        print(f"\n📊 Found {len(rankings)} rankings")
        print(f"\nShowing top {min(limit, len(rankings))} results:\n")
        
        # Display top results
        for i, ranking in enumerate(rankings[:limit], 1):
            if not isinstance(ranking, dict):
                continue
                
            print(f"{i}. {ranking.get('name', 'Unknown')}")
            print(f"   Class: {ranking.get('class', 'Unknown')} ({ranking.get('spec', 'Unknown')})")
            print(f"   Amount: {ranking.get('amount', 0):,}")
            
            # Check for report code
            report = ranking.get('report', {})
            if isinstance(report, dict):
                code = report.get('code')
                fight_id = report.get('fightID', report.get('fightId'))
                if code:
                    print(f"   ✅ Report Code: {code} (Fight {fight_id})")
                    print(f"      URL: https://www.esologs.com/reports/{code}#{fight_id}")
                else:
                    print(f"   ❌ No report code")
            print()
        
        # Check how many have report codes
        reports_with_codes = [
            r for r in rankings 
            if isinstance(r, dict) and 
            isinstance(r.get('report'), dict) and 
            r.get('report', {}).get('code')
        ]
        
        print(f"📋 Summary:")
        print(f"   Total rankings: {len(rankings)}")
        print(f"   With report codes: {len(reports_with_codes)}")
        print(f"   Without codes: {len(rankings) - len(reports_with_codes)}")
        
        # Show unique report codes
        unique_codes = set(
            r['report']['code'] 
            for r in reports_with_codes
        )
        print(f"   Unique reports: {len(unique_codes)}")
    
    async def compare_queries(self, encounter_id: int, limit: int = 5):
        """Compare different query types side-by-side."""
        print("\n" + "="*80)
        print("COMPARING DIFFERENT QUERY TYPES")
        print("="*80)
        
        # Test configurations
        tests = [
            {
                "name": "characterRankings with dps (no leaderboard)",
                "query_type": "characterRankings",
                "metric": "dps",
                "leaderboard": None
            },
            {
                "name": "characterRankings with dps + LogsOnly",
                "query_type": "characterRankings",
                "metric": "dps",
                "leaderboard": "LogsOnly"
            },
            {
                "name": "characterRankings with hps + LogsOnly",
                "query_type": "characterRankings",
                "metric": "hps",
                "leaderboard": "LogsOnly"
            },
        ]
        
        results = {}
        for test in tests:
            await asyncio.sleep(1)  # Rate limiting
            result = await self.test_query(
                query_type=test["query_type"],
                encounter_id=encounter_id,
                metric=test["metric"],
                leaderboard=test["leaderboard"],
                limit=limit
            )
            results[test["name"]] = result
        
        return results
    
    async def close(self):
        """Close the API client."""
        await self.client.close()


async def main():
    """Main entry point."""
    print("\n" + "="*80)
    print("ESO LOGS QUERY TESTER")
    print("="*80)
    
    # Default test: The Mage (Aetherian Archive final boss)
    encounter_id = 4
    encounter_name = "The Mage"
    
    # Allow command-line override
    if len(sys.argv) > 1:
        encounter_id = int(sys.argv[1])
        encounter_name = f"Encounter {encounter_id}"
    
    print(f"\nTesting with: {encounter_name} (ID: {encounter_id})")
    
    tester = QueryTester()
    
    try:
        # Test current working query
        print("\n" + "="*80)
        print("CURRENT WORKING QUERY")
        print("="*80)
        await tester.test_query(
            query_type="characterRankings",
            encounter_id=encounter_id,
            metric="dps",
            leaderboard="LogsOnly",
            limit=10
        )
        
        # Uncomment to compare multiple queries
        # print("\n\n")
        # await tester.compare_queries(encounter_id, limit=5)
        
    finally:
        await tester.close()
    
    print("\n" + "="*80)
    print("Testing Complete!")
    print("="*80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())

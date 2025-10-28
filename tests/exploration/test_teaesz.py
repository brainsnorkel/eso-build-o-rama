#!/usr/bin/env python3
"""
Quick test to verify @TeaEsz appears in our data
"""

import asyncio
import sys
sys.path.insert(0, '.')

from src.eso_build_o_rama.api_client import ESOLogsAPIClient
from src.eso_build_o_rama.data_parser import DataParser
from src.eso_build_o_rama.build_analyzer import BuildAnalyzer

async def test_teaesz():
    client = ESOLogsAPIClient()
    parser = DataParser()
    
    print("🔍 Testing for @TeaEsz in Firstmage Nullifier rankings")
    print("="*60)
    
    # Get top rankings for Firstmage Nullifier
    rankings = await client.get_top_logs(zone_id=1, encounter_id=4, limit=5)
    
    print(f"\n✅ Found {len(rankings)} top-ranked reports:")
    for i, rank in enumerate(rankings, 1):
        name = rank.get('name', '')
        dps = rank.get('amount', 0)
        report_code = rank.get('report', {}).get('code', '')
        print(f"{i}. {name} - {dps:,} DPS - {report_code}")
    
    # Check if TeaEsz's report is in the list
    teaesz_report = 'zg1LvMptm7bTnAkK'
    teaesz_in_rankings = any(r.get('report', {}).get('code') == teaesz_report for r in rankings)
    
    if teaesz_in_rankings:
        print(f"\n✅✅✅ @TeaEsz's report ({teaesz_report}) IS in top 5!")
        
        # Now process this report
        print(f"\n📊 Processing @TeaEsz's report...")
        report_data = await client.get_report(teaesz_report)
        
        if report_data:
            fights = report_data.get('fights', [])
            print(f"   Report has {len(fights)} fights")
            
            # Find Firstmage Nullifier fight
            for fight in fights:
                if 'Nullifier' in fight['name']:
                    print(f"\n   Processing fight: {fight['name']} (ID: {fight['id']})")
                    
                    # Get table data
                    table_data = await client.get_report_table(
                        report_code=teaesz_report,
                        start_time=fight['startTime'],
                        end_time=fight['endTime'],
                        include_combatant_info=True
                    )
                    
                    # Parse players
                    players = parser.parse_report_data(
                        report_data,
                        table_data,
                        fight['id']
                    )
                    
                    print(f"   Parsed {len(players)} players")
                    
                    # Analyze builds
                    analyzer = BuildAnalyzer()
                    for player in players:
                        analyzer._analyze_player_build(player)
                    
                    # Look for Book Enthusiast / TeaEsz
                    for player in players:
                        if 'tea' in player.character_name.lower() or 'tea' in player.player_name.lower() or 'book enthusiast' in player.character_name.lower():
                            print(f"\n   ✅✅✅ FOUND @TEAESZ!")
                            print(f"      Character: {player.character_name}")
                            print(f"      Player: {player.player_name}")
                            print(f"      DPS: {player.dps:,}")
                            print(f"      Class: {player.class_name}")
                            print(f"      Subclasses: {' / '.join(player.subclasses)}")
                            print(f"      Sets: {', '.join(player.sets_equipped.keys())}")
                            print(f"      Build Slug: {player.get_build_slug()}")
                    
                    break
    else:
        print(f"\n❌ @TeaEsz's report ({teaesz_report}) NOT in top 5")
        print("   This means our rankings query might not be working correctly")
    
    await client.close()

asyncio.run(test_teaesz())

#!/usr/bin/env python3
"""
Build Inspector Utility
Analyze what builds were found for a specific boss and why they were/weren't published.
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Dict, Any, List
from collections import defaultdict

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.eso_build_o_rama.api_client import ESOLogsAPIClient
from src.eso_build_o_rama.data_parser import DataParser
from src.eso_build_o_rama.build_analyzer import BuildAnalyzer
from src.eso_build_o_rama.models import PlayerBuild
from dotenv import load_dotenv

load_dotenv()


class BuildInspector:
    """Inspect builds found for a specific boss."""
    
    def __init__(self):
        """Initialize the inspector."""
        self.client = ESOLogsAPIClient()
        self.parser = DataParser()
        self.analyzer = BuildAnalyzer()
    
    async def inspect_boss_builds(
        self,
        trial_name: str,
        boss_name: str,
        encounter_id: int,
        num_reports: int = 12
    ):
        """
        Analyze all builds found for a specific boss.
        
        Args:
            trial_name: Name of the trial
            boss_name: Name of the boss
            encounter_id: Encounter ID for the boss
            num_reports: Number of top reports to analyze
        """
        print(f"\n{'='*80}")
        print(f"BUILD INSPECTOR: {trial_name} - {boss_name}")
        print(f"{'='*80}\n")
        
        # Get top reports
        print(f"Fetching top {num_reports} reports for encounter {encounter_id}...")
        top_reports = await self.client.get_top_logs(
            zone_id=1,  # Would need to map trial name to zone ID
            encounter_id=encounter_id,
            limit=num_reports
        )
        
        if not top_reports:
            print("❌ No reports found!")
            return
        
        print(f"✅ Found {len(top_reports)} top-ranked reports\n")
        
        # Collect all players from all reports
        all_players = []
        successful_reports = 0
        
        for i, report_data in enumerate(top_reports, 1):
            report_code = report_data.get('code')
            fight_id = report_data.get('fightID')
            
            print(f"Report {i}/{len(top_reports)}: {report_code} (fight {fight_id})")
            
            # Fetch and process this report
            report = await self.client.get_report(report_code)
            if not report:
                print("  ❌ Failed to fetch report")
                continue
            
            # Find the fight
            fight_info = None
            for fight in report.get('fights', []):
                if fight.get('id') == fight_id:
                    fight_info = fight
                    break
            
            if not fight_info:
                print(f"  ❌ Fight {fight_id} not found")
                continue
            
            # Verify it's the right boss
            if fight_info.get('name') != boss_name:
                print(f"  ⚠️  Fight is '{fight_info.get('name')}', not '{boss_name}'")
                continue
            
            # Fetch table data
            summary_data = await self.client.get_report_table(
                report_code=report_code,
                start_time=fight_info.get('startTime'),
                end_time=fight_info.get('endTime'),
                data_type="Summary",
                include_combatant_info=True
            )
            
            damage_data = await self.client.get_report_table(
                report_code=report_code,
                start_time=fight_info.get('startTime'),
                end_time=fight_info.get('endTime'),
                data_type="DamageDone",
                include_combatant_info=True
            )
            
            # Parse players
            players = self.parser.parse_report_data(
                report,
                damage_data,
                fight_id,
                player_details_data=summary_data
            )
            
            if not players:
                print(f"  ❌ No players parsed")
                continue
            
            print(f"  ✅ Found {len(players)} players")
            all_players.extend(players)
            successful_reports += 1
        
        if not all_players:
            print("\n❌ No players found across all reports!")
            return
        
        print(f"\n{'='*80}")
        print(f"ANALYSIS SUMMARY")
        print(f"{'='*80}\n")
        print(f"Total players collected: {len(all_players)}")
        print(f"Successful reports: {successful_reports}/{len(top_reports)}")
        
        # Analyze builds
        print(f"\nAnalyzing builds...")
        for player in all_players:
            self.analyzer._analyze_player_build(player)
        
        # Debug: Show first player details
        if all_players:
            p = all_players[0]
            print(f"\nFirst player example:")
            print(f"  Name: {p.character_name}")
            print(f"  Class: {p.class_name}")
            print(f"  Role: {p.role}")
            print(f"  Subclasses: {p.subclasses}")
            print(f"  Sets: {p.sets_equipped}")
            print(f"  build_slug: '{p.get_build_slug()}'")
            print(f"  Gear pieces: {len(p.gear)}")
            print(f"  Bar 1 abilities: {len(p.abilities_bar1)}")
            print(f"  Bar 2 abilities: {len(p.abilities_bar2)}")
        
        # Group by build slug (using the get_build_slug() method)
        build_groups = defaultdict(list)
        for player in all_players:
            build_slug = player.get_build_slug()
            if build_slug:
                build_groups[build_slug].append(player)
        
        print(f"\n{'='*80}")
        print(f"BUILDS FOUND")
        print(f"{'='*80}\n")
        
        # Sort by count
        sorted_builds = sorted(build_groups.items(), key=lambda x: len(x[1]), reverse=True)
        
        for i, (build_slug, players) in enumerate(sorted_builds, 1):
            count = len(players)
            
            # Determine publishable status
            # Check if this is DPS, tank, or healer
            example_player = players[0]
            role = example_player.role if hasattr(example_player, 'role') else 'DPS'
            
            # Thresholds from build_analyzer
            if role == 'DPS':
                threshold = 5
            else:  # Tank or Healer
                threshold = 3
            
            is_publishable = count >= threshold
            status = "✅ PUBLISHABLE" if is_publishable else f"❌ NOT PUBLISHABLE (need {threshold - count} more)"
            
            print(f"{i}. {build_slug}")
            print(f"   Players: {count} | {status}")
            print(f"   Role: {role}")
            
            # Show example player details
            if players:
                p = players[0]
                print(f"   Class: {p.class_name}")
                if p.subclasses:
                    print(f"   Subclasses: {'/'.join(p.subclasses)}")
                
                # Show gear sets
                sets = {}
                for gear in p.gear:
                    set_name = gear.set_name
                    if set_name and set_name != "Unknown":
                        sets[set_name] = sets.get(set_name, 0) + 1
                
                if sets:
                    print(f"   Sets: {', '.join(f'{name} ({count})' for name, count in sorted(sets.items(), key=lambda x: x[1], reverse=True))}")
            
            print()
        
        # Summary
        publishable = sum(1 for _, players in sorted_builds if len(players) >= 5)
        print(f"{'='*80}")
        print(f"Total unique builds: {len(sorted_builds)}")
        print(f"Publishable (5+ players): {publishable}")
        print(f"Not publishable: {len(sorted_builds) - publishable}")
        print(f"{'='*80}\n")
    
    async def close(self):
        """Close the API client."""
        await self.client.close()


async def main():
    """Main entry point."""
    # Default: The Mage from Aetherian Archive
    trial_name = "Aetherian Archive"
    boss_name = "The Mage"
    encounter_id = 4
    
    # Allow command-line override
    if len(sys.argv) > 1:
        encounter_id = int(sys.argv[1])
    if len(sys.argv) > 2:
        boss_name = sys.argv[2]
    if len(sys.argv) > 3:
        trial_name = sys.argv[3]
    
    inspector = BuildInspector()
    
    try:
        await inspector.inspect_boss_builds(
            trial_name=trial_name,
            boss_name=boss_name,
            encounter_id=encounter_id,
            num_reports=12
        )
    finally:
        await inspector.close()


if __name__ == "__main__":
    asyncio.run(main())

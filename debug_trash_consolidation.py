#!/usr/bin/env python3
"""
Debug script to examine trash build consolidation.
"""

import asyncio
import json
from src.eso_build_o_rama.trial_scanner import TrialScanner

async def debug_trash_consolidation():
    """Debug trash build consolidation."""
    
    # Initialize scanner
    scanner = TrialScanner()
    
    try:
        # Load trial data
        with open('data/trials.json', 'r') as f:
            trials_data = json.load(f)
        
        # Find Aetherian Archive trial
        aa_trial = None
        for trial in trials_data['trials']:
            if trial['name'] == 'Aetherian Archive':
                aa_trial = trial
                break
        
        if not aa_trial:
            print("Aetherian Archive trial not found!")
            return
            
        # Scan Aetherian Archive
        print("Scanning Aetherian Archive...")
        all_reports = await scanner.scan_all_trials([aa_trial])
        
        # Get publishable builds
        print("Getting publishable builds...")
        publishable_builds = await scanner.get_publishable_builds(all_reports)
        
        print(f"Total publishable builds: {len(publishable_builds)}")
        
        # Check for trash builds
        trash_builds = [build for build in publishable_builds if build.boss_name == "Trash Builds"]
        print(f"Trash builds in publishable: {len(trash_builds)}")
        
        # Check all builds to see what boss names exist
        boss_names = set()
        for build in publishable_builds:
            boss_names.add(build.boss_name)
        
        print(f"Boss names in publishable builds: {sorted(boss_names)}")
        
        # Check if there are any trash builds that didn't make it to publishable
        all_trash_reports = []
        for trial_name, reports in all_reports.items():
            for report in reports:
                if report.boss_name == "Trash Builds":
                    all_trash_reports.append(report)
        
        print(f"Total trash reports found: {len(all_trash_reports)}")
        
        if all_trash_reports:
            print("Trash reports details:")
            for i, report in enumerate(all_trash_reports):
                print(f"  Report {i+1}: {report.report_code}")
                print(f"    Players: {len(report.all_players)}")
                print(f"    Common builds: {len(report.common_builds)}")
                
                # Check common builds
                for build in report.common_builds:
                    print(f"      Build: {build.build_slug}")
                    print(f"        Count: {build.count}")
                    print(f"        Best player role: {build.best_player.role if build.best_player else 'None'}")
                    print(f"        Meets threshold: {build.meets_threshold()}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await scanner.close()

if __name__ == "__main__":
    asyncio.run(debug_trash_consolidation())

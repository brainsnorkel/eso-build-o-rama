#!/usr/bin/env python3
"""
Test script to verify mundus detection implementation.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from eso_build_o_rama.api_client import ESOLogsAPIClient
from eso_build_o_rama.cache_manager import CacheManager

async def test_mundus_detection():
    """Test the mundus detection functionality."""
    
    # Initialize cache manager and API client
    cache_manager = CacheManager()
    api_client = ESOLogsAPIClient(cache_manager=cache_manager)
    
    try:
        # Test with a known report (using Sanity's Edge as example)
        report_code = "xb7TKHXR8DJByp4Q"  # This should be a real report code
        fight_id = 17
        player_name = "@revloh"  # Known player from SE
        start_time = 2614035
        end_time = 2777081
        
        print(f"Testing mundus detection for {player_name} in report {report_code}")
        
        # Test the get_player_buffs method
        mundus_stone = await api_client.get_player_buffs(
            report_code=report_code,
            fight_ids=[fight_id],
            player_name=player_name,
            start_time=start_time,
            end_time=end_time
        )
        
        print(f"Result: {mundus_stone}")
        
        if mundus_stone:
            print(f"✅ Successfully detected mundus stone: {mundus_stone}")
        else:
            print("⚠️  No mundus stone detected (this might be expected if player has no Boon buffs)")
            
    except Exception as e:
        print(f"❌ Error testing mundus detection: {e}")
    
    finally:
        await api_client.close()

if __name__ == "__main__":
    print("Testing mundus detection implementation...")
    asyncio.run(test_mundus_detection())

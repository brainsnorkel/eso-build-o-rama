"""
Tests for ESO Logs API client.
"""

import sys
import os
import pytest
import asyncio

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.eso_build_o_rama.api_client import ESOLogsAPIClient


@pytest.mark.asyncio
async def test_api_authentication():
    """Test that we can authenticate with the API."""
    client = ESOLogsAPIClient()
    assert client.client is not None
    assert client.client_id is not None
    assert client.client_secret is not None
    assert client.access_token is not None
    await client.close()


@pytest.mark.asyncio
async def test_get_zones():
    """Test fetching available zones."""
    client = ESOLogsAPIClient()
    
    zones = await client.get_zones()
    
    assert isinstance(zones, list)
    assert len(zones) > 0
    
    # Check structure of first zone
    first_zone = zones[0]
    assert "id" in first_zone
    assert "name" in first_zone
    
    print(f"\nFound {len(zones)} zones")
    print(f"First zone: {first_zone['name']} (ID: {first_zone['id']})")
    
    await client.close()


if __name__ == "__main__":
    # Run a simple test manually
    async def main():
        print("Testing ESO Logs API client...")
        client = ESOLogsAPIClient()
        
        print("\n1. Fetching zones...")
        zones = await client.get_zones()
        print(f"   Found {len(zones)} zones")
        
        # Show trial zones (likely to be relevant)
        trial_keywords = ["trial", "raid", "sanctum", "archive", "citadel", 
                          "fabrication", "asylum", "cloudrest", "sunspire", 
                          "aegis", "rockgrove", "reef", "edge", "lucent"]
        
        print("\n2. Trial zones:")
        for zone in zones:
            zone_name = zone.get("name", "").lower()
            if any(keyword in zone_name for keyword in trial_keywords):
                encounters = zone.get("encounters", [])
                print(f"   - {zone['name']} (ID: {zone['id']}, {len(encounters)} encounters)")
        
        await client.close()
        print("\n✅ API client test complete!")
    
    asyncio.run(main())

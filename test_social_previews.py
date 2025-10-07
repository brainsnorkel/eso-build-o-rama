#!/usr/bin/env python3
"""
Test script for social media preview generation.
"""

import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from eso_build_o_rama.social_preview_generator import SocialPreviewGenerator

def main():
    """Test social media preview generation."""
    print("Testing social media preview generation...")
    
    generator = SocialPreviewGenerator()
    
    # Test main preview generation
    print("Generating main preview...")
    main_preview = generator.create_main_preview(is_develop=False)
    print(f"✓ Generated main preview: {main_preview}")
    
    # Test development preview
    print("Generating development preview...")
    dev_preview = generator.create_main_preview(is_develop=True)
    print(f"✓ Generated dev preview: {dev_preview}")
    
    # Test build-specific preview
    print("Generating build-specific preview...")
    build_preview = generator.create_build_preview(
        build_name="Magicka Sorcerer",
        trial_name="Hel Ra Citadel", 
        boss_name="The Warrior",
        dps="120,000",
        player_name="TopPlayer",
        is_develop=False
    )
    print(f"✓ Generated build preview: {build_preview}")
    
    print("\nAll social media previews generated successfully!")
    print("Check the static/ directory for the generated images.")

if __name__ == "__main__":
    main()

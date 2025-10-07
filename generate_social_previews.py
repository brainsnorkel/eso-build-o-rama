#!/usr/bin/env python3
"""
Generate social media preview images for the ESO Build-o-rama site.
"""

import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from eso_build_o_rama.social_preview_generator import generate_social_previews

def main():
    """Generate social media preview images."""
    # Check if this is development mode
    is_develop = len(sys.argv) > 1 and sys.argv[1] == "--dev"
    
    print(f"Generating social media preview images... (Development mode: {is_develop})")
    generate_social_previews(is_develop)
    print("Social media preview images generated successfully!")

if __name__ == "__main__":
    main()

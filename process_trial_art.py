#!/usr/bin/env python3
"""
Process trial artwork for use in:
1. Trial box backgrounds on home page (faint alpha blend)
2. Social card backgrounds (1200x630px)
3. Site banner background in header
"""

from PIL import Image, ImageEnhance
import os
from pathlib import Path

# Directories
SOURCE_DIR = Path("eso-art")
STATIC_DIR = Path("static")
TRIAL_BG_DIR = STATIC_DIR / "trial-backgrounds"
SOCIAL_BG_DIR = STATIC_DIR / "social-backgrounds"
BANNER_DIR = STATIC_DIR / "banners"

# Create output directories
TRIAL_BG_DIR.mkdir(parents=True, exist_ok=True)
SOCIAL_BG_DIR.mkdir(parents=True, exist_ok=True)
BANNER_DIR.mkdir(parents=True, exist_ok=True)

# Trial box background settings
TRIAL_BOX_WIDTH = 600  # Max width for trial boxes
TRIAL_BOX_ALPHA = 0.35  # Brighter for trial links

# Social card settings
SOCIAL_WIDTH = 1200
SOCIAL_HEIGHT = 630
SOCIAL_ALPHA = 0.3  # More visible for social cards

# Banner settings
BANNER_HEIGHT = 120  # Height of header
BANNER_ALPHA = 0.35  # Brighter background for site/builds


def process_trial_background(source_path: Path, output_path: Path):
    """
    Process trial image for use as faint background in trial boxes.
    Resize to fit box width and apply heavy alpha transparency.
    """
    print(f"Processing trial background: {source_path.name}")
    
    with Image.open(source_path) as img:
        # Convert to RGBA if not already
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        
        # Resize maintaining aspect ratio
        aspect_ratio = img.height / img.width
        new_height = int(TRIAL_BOX_WIDTH * aspect_ratio)
        img = img.resize((TRIAL_BOX_WIDTH, new_height), Image.Resampling.LANCZOS)
        
        # Apply alpha transparency
        alpha = img.split()[3]
        alpha = ImageEnhance.Brightness(alpha).enhance(TRIAL_BOX_ALPHA)
        img.putalpha(alpha)
        
        # Save as PNG
        img.save(output_path, 'PNG', optimize=True)
        print(f"  ✓ Saved: {output_path}")


def process_social_background(source_path: Path, output_path: Path):
    """
    Process trial image for use as social card background (1200x630).
    Center crop and apply moderate alpha transparency.
    """
    print(f"Processing social background: {source_path.name}")
    
    with Image.open(source_path) as img:
        # Convert to RGBA if not already
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        
        # Calculate dimensions for center crop
        target_aspect = SOCIAL_WIDTH / SOCIAL_HEIGHT
        img_aspect = img.width / img.height
        
        if img_aspect > target_aspect:
            # Image is wider - crop width
            new_width = int(img.height * target_aspect)
            left = (img.width - new_width) // 2
            img = img.crop((left, 0, left + new_width, img.height))
        else:
            # Image is taller - crop height
            new_height = int(img.width / target_aspect)
            top = (img.height - new_height) // 2
            img = img.crop((0, top, img.width, top + new_height))
        
        # Resize to social card dimensions
        img = img.resize((SOCIAL_WIDTH, SOCIAL_HEIGHT), Image.Resampling.LANCZOS)
        
        # Apply alpha transparency
        alpha = img.split()[3]
        alpha = ImageEnhance.Brightness(alpha).enhance(SOCIAL_ALPHA)
        img.putalpha(alpha)
        
        # Save as PNG
        img.save(output_path, 'PNG', optimize=True)
        print(f"  ✓ Saved: {output_path}")


def process_banner(source_path: Path, output_path: Path):
    """
    Process site banner for header background.
    Crop to banner height and apply faint alpha transparency.
    Right-aligned crop for character positioning.
    """
    print(f"Processing site banner: {source_path.name}")
    
    with Image.open(source_path) as img:
        # Convert to RGBA if not already
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        
        # Calculate dimensions for right-aligned crop
        aspect_ratio = img.width / img.height
        new_width = int(BANNER_HEIGHT * aspect_ratio)
        
        # Resize maintaining aspect ratio
        img = img.resize((new_width, BANNER_HEIGHT), Image.Resampling.LANCZOS)
        
        # Crop from right side (keep rightmost portion with character)
        # Take a reasonable width (e.g., 1200px or full width if smaller)
        crop_width = min(1200, new_width)
        left = new_width - crop_width
        img = img.crop((left, 0, new_width, BANNER_HEIGHT))
        
        # Apply alpha transparency
        alpha = img.split()[3]
        alpha = ImageEnhance.Brightness(alpha).enhance(BANNER_ALPHA)
        img.putalpha(alpha)
        
        # Save as PNG
        img.save(output_path, 'PNG', optimize=True)
        print(f"  ✓ Saved: {output_path}")


def main():
    """Process all trial artwork."""
    print("=" * 70)
    print("ESO TRIAL ARTWORK PROCESSOR")
    print("=" * 70)
    print()
    
    # Process trial images
    trial_files = [
        f for f in SOURCE_DIR.glob("*.png")
        if f.name != "site_banner_characterload.png"
    ]
    
    print(f"Found {len(trial_files)} trial images to process")
    print()
    
    for trial_file in sorted(trial_files):
        base_name = trial_file.stem
        
        # Process for trial box background
        trial_bg_output = TRIAL_BG_DIR / f"{base_name}.png"
        process_trial_background(trial_file, trial_bg_output)
        
        # Process for social card background
        social_bg_output = SOCIAL_BG_DIR / f"{base_name}.png"
        process_social_background(trial_file, social_bg_output)
        
        print()
    
    # Process site banner
    banner_file = SOURCE_DIR / "site_banner_characterload.png"
    if banner_file.exists():
        print("Processing site banner")
        banner_output = BANNER_DIR / "site_banner.png"
        process_banner(banner_file, banner_output)
        print()
    
    print("=" * 70)
    print("✓ All artwork processed successfully!")
    print("=" * 70)
    print()
    print("Output directories:")
    print(f"  - Trial backgrounds: {TRIAL_BG_DIR}")
    print(f"  - Social backgrounds: {SOCIAL_BG_DIR}")
    print(f"  - Site banner: {BANNER_DIR}")


if __name__ == "__main__":
    main()


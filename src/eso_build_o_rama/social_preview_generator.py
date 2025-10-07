"""
Social Media Preview Image Generator
Creates attractive preview images for social media sharing.
"""

import logging
from pathlib import Path
from typing import Optional, Tuple
from PIL import Image, ImageDraw, ImageFont
import textwrap

logger = logging.getLogger(__name__)


class SocialPreviewGenerator:
    """Generates social media preview images for the ESO Build-o-rama site."""
    
    def __init__(self, static_dir: str = "static"):
        """
        Initialize the social preview generator.
        
        Args:
            static_dir: Directory containing static assets
        """
        self.static_dir = Path(static_dir)
        self.static_dir.mkdir(exist_ok=True)
        
        # Standard social media image dimensions (Twitter/Facebook)
        self.image_width = 1200
        self.image_height = 630
        
    def create_main_preview(self, is_develop: bool = False) -> Path:
        """
        Create the main social media preview image.
        
        Args:
            is_develop: Whether this is for development environment
            
        Returns:
            Path to the generated image
        """
        # Create image with gradient background
        img = Image.new('RGB', (self.image_width, self.image_height), color='#1a1a2e')
        draw = ImageDraw.Draw(img)
        
        # Color scheme
        if is_develop:
            primary_color = '#f39c12'
            secondary_color = '#e67e22'
            accent_color = '#f1c40f'
        else:
            primary_color = '#11998e'
            secondary_color = '#38ef7d'
            accent_color = '#a8edea'
        
        # Draw gradient background
        self._draw_gradient_background(draw, primary_color, secondary_color)
        
        # Try to load fonts, fallback to default if not available
        try:
            title_font = ImageFont.truetype("/System/Library/Fonts/Arial Bold.ttf", 72)
            subtitle_font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 36)
            description_font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 28)
        except (OSError, IOError):
            try:
                title_font = ImageFont.truetype("arial.ttf", 72)
                subtitle_font = ImageFont.truetype("arial.ttf", 36)
                description_font = ImageFont.truetype("arial.ttf", 28)
            except (OSError, IOError):
                # Fallback to default font
                title_font = ImageFont.load_default()
                subtitle_font = ImageFont.load_default()
                description_font = ImageFont.load_default()
        
        # Main title
        title_text = "ESO Build-o-rama"
        if is_develop:
            title_text += " [DEV]"
        
        title_bbox = draw.textbbox((0, 0), title_text, font=title_font)
        title_width = title_bbox[2] - title_bbox[0]
        title_x = (self.image_width - title_width) // 2
        title_y = 120
        
        # Draw title with shadow effect
        draw.text((title_x + 3, title_y + 3), title_text, fill='#000000', font=title_font)
        draw.text((title_x, title_y), title_text, fill='#ffffff', font=title_font)
        
        # Subtitle
        subtitle_text = "Meta Build Explorer"
        subtitle_bbox = draw.textbbox((0, 0), subtitle_text, font=subtitle_font)
        subtitle_width = subtitle_bbox[2] - subtitle_bbox[0]
        subtitle_x = (self.image_width - subtitle_width) // 2
        subtitle_y = title_y + 90
        
        draw.text((subtitle_x, subtitle_y), subtitle_text, fill=accent_color, font=subtitle_font)
        
        # Description
        description_lines = [
            "Discover the most effective ESO builds from",
            "top-performing players. Explore meta builds,",
            "gear sets, and strategies for all trials."
        ]
        
        description_y = subtitle_y + 80
        for i, line in enumerate(description_lines):
            line_bbox = draw.textbbox((0, 0), line, font=description_font)
            line_width = line_bbox[2] - line_bbox[0]
            line_x = (self.image_width - line_width) // 2
            draw.text((line_x, description_y + (i * 40)), line, fill='#e8e8e8', font=description_font)
        
        # Add ESO-style decorative elements
        self._draw_decorative_elements(draw, primary_color, accent_color)
        
        # Save image
        filename = "social-preview-dev.png" if is_develop else "social-preview.png"
        output_path = self.static_dir / filename
        img.save(output_path, "PNG", optimize=True)
        
        logger.info(f"Generated social preview image: {output_path}")
        return output_path
    
    def create_build_preview(self, build_name: str, trial_name: str, boss_name: str, 
                           dps: str, player_name: str, is_develop: bool = False) -> Path:
        """
        Create a preview image for a specific build.
        
        Args:
            build_name: Name of the build
            trial_name: Name of the trial
            boss_name: Name of the boss
            dps: DPS value
            player_name: Name of the player
            is_develop: Whether this is for development environment
            
        Returns:
            Path to the generated image
        """
        # Create image with gradient background
        img = Image.new('RGB', (self.image_width, self.image_height), color='#1a1a2e')
        draw = ImageDraw.Draw(img)
        
        # Color scheme
        if is_develop:
            primary_color = '#f39c12'
            secondary_color = '#e67e22'
            accent_color = '#f1c40f'
        else:
            primary_color = '#11998e'
            secondary_color = '#38ef7d'
            accent_color = '#a8edea'
        
        # Draw gradient background
        self._draw_gradient_background(draw, primary_color, secondary_color)
        
        # Try to load fonts
        try:
            title_font = ImageFont.truetype("/System/Library/Fonts/Arial Bold.ttf", 60)
            subtitle_font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 32)
            info_font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 24)
        except (OSError, IOError):
            try:
                title_font = ImageFont.truetype("arial.ttf", 60)
                subtitle_font = ImageFont.truetype("arial.ttf", 32)
                info_font = ImageFont.truetype("arial.ttf", 24)
            except (OSError, IOError):
                title_font = ImageFont.load_default()
                subtitle_font = ImageFont.load_default()
                info_font = ImageFont.load_default()
        
        # Build title
        title_text = build_name
        title_bbox = draw.textbbox((0, 0), title_text, font=title_font)
        title_width = title_bbox[2] - title_bbox[0]
        title_x = (self.image_width - title_width) // 2
        title_y = 80
        
        # Draw title with shadow
        draw.text((title_x + 2, title_y + 2), title_text, fill='#000000', font=title_font)
        draw.text((title_x, title_y), title_text, fill='#ffffff', font=title_font)
        
        # Trial and boss
        trial_boss_text = f"{trial_name} - {boss_name}"
        trial_boss_bbox = draw.textbbox((0, 0), trial_boss_text, font=subtitle_font)
        trial_boss_width = trial_boss_bbox[2] - trial_boss_bbox[0]
        trial_boss_x = (self.image_width - trial_boss_width) // 2
        trial_boss_y = title_y + 80
        
        draw.text((trial_boss_x, trial_boss_y), trial_boss_text, fill=accent_color, font=subtitle_font)
        
        # DPS highlight
        dps_text = f"{dps} DPS"
        dps_bbox = draw.textbbox((0, 0), dps_text, font=subtitle_font)
        dps_width = dps_bbox[2] - dps_bbox[0]
        dps_x = (self.image_width - dps_width) // 2
        dps_y = trial_boss_y + 60
        
        # Draw DPS with glow effect
        for offset in range(3, 0, -1):
            draw.text((dps_x + offset, dps_y + offset), dps_text, fill='#ff6b6b', font=subtitle_font)
        draw.text((dps_x, dps_y), dps_text, fill='#ff6b6b', font=subtitle_font)
        
        # Player info
        player_text = f"by {player_name}"
        player_bbox = draw.textbbox((0, 0), player_text, font=info_font)
        player_width = player_bbox[2] - player_bbox[0]
        player_x = (self.image_width - player_width) // 2
        player_y = dps_y + 60
        
        draw.text((player_x, player_y), player_text, fill='#e8e8e8', font=info_font)
        
        # Add decorative elements
        self._draw_decorative_elements(draw, primary_color, accent_color)
        
        # Save image
        filename = f"social-preview-build-dev.png" if is_develop else "social-preview-build.png"
        output_path = self.static_dir / filename
        img.save(output_path, "PNG", optimize=True)
        
        logger.info(f"Generated build preview image: {output_path}")
        return output_path
    
    def _draw_gradient_background(self, draw: ImageDraw.Draw, color1: str, color2: str):
        """Draw a gradient background."""
        # Simple gradient simulation
        for y in range(self.image_height):
            ratio = y / self.image_height
            r1, g1, b1 = self._hex_to_rgb(color1)
            r2, g2, b2 = self._hex_to_rgb(color2)
            
            r = int(r1 + (r2 - r1) * ratio)
            g = int(g1 + (g2 - g1) * ratio)
            b = int(b1 + (b2 - b1) * ratio)
            
            draw.line([(0, y), (self.image_width, y)], fill=(r, g, b))
    
    def _draw_decorative_elements(self, draw: ImageDraw.Draw, primary_color: str, accent_color: str):
        """Add decorative elements to the image."""
        # Add some geometric shapes for visual interest
        # Top corners
        draw.ellipse([50, 50, 150, 150], outline=accent_color, width=3)
        draw.ellipse([self.image_width - 150, 50, self.image_width - 50, 150], outline=accent_color, width=3)
        
        # Bottom corners
        draw.ellipse([50, self.image_height - 150, 150, self.image_height - 50], outline=accent_color, width=3)
        draw.ellipse([self.image_width - 150, self.image_height - 150, self.image_width - 50, self.image_height - 50], outline=accent_color, width=3)
        
        # Add some lines
        draw.line([(100, self.image_height // 2), (300, self.image_height // 2)], fill=primary_color, width=2)
        draw.line([(self.image_width - 300, self.image_height // 2), (self.image_width - 100, self.image_height // 2)], fill=primary_color, width=2)
    
    def _hex_to_rgb(self, hex_color: str) -> Tuple[int, int, int]:
        """Convert hex color to RGB tuple."""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def generate_social_previews(is_develop: bool = False):
    """
    Generate all social media preview images.
    
    Args:
        is_develop: Whether this is for development environment
    """
    generator = SocialPreviewGenerator()
    
    # Generate main preview
    main_preview = generator.create_main_preview(is_develop)
    print(f"Generated main social preview: {main_preview}")
    
    # Generate example build preview
    build_preview = generator.create_build_preview(
        build_name="Magicka Sorcerer",
        trial_name="Hel Ra Citadel",
        boss_name="The Warrior",
        dps="120,000",
        player_name="TopPlayer",
        is_develop=is_develop
    )
    print(f"Generated build preview: {build_preview}")


if __name__ == "__main__":
    import sys
    is_develop = len(sys.argv) > 1 and sys.argv[1] == "--dev"
    generate_social_previews(is_develop)

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
    """Generates social media preview images for the ESOBuild.com site."""
    
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
        # Create image with site banner background
        img = self._create_background_with_banner()
        draw = ImageDraw.Draw(img)
        
        # Color scheme for decorative elements
        if is_develop:
            primary_color = '#f39c12'
            secondary_color = '#e67e22'
            accent_color = '#f1c40f'
        else:
            primary_color = '#11998e'
            secondary_color = '#38ef7d'
            accent_color = '#a8edea'
        
        # Try to load fonts, fallback to default if not available
        # Increased sizes for better readability over background images
        try:
            title_font = ImageFont.truetype("/System/Library/Fonts/Arial Bold.ttf", 96)
            subtitle_font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 48)
            description_font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 36)
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
        title_text = "ESOBuild.com"
        if is_develop:
            title_text += "[DEV]"
        
        title_bbox = draw.textbbox((0, 0), title_text, font=title_font)
        title_width = title_bbox[2] - title_bbox[0]
        title_x = (self.image_width - title_width) // 2
        title_y = 120
        
        # Draw title with shadow effect
        draw.text((title_x + 3, title_y + 3), title_text, fill='#000000', font=title_font)
        draw.text((title_x, title_y), title_text, fill='#ffffff', font=title_font)
        
        # Subtitle
        subtitle_text = "ESOLogs-driven Meta Build Explorer"
        subtitle_bbox = draw.textbbox((0, 0), subtitle_text, font=subtitle_font)
        subtitle_width = subtitle_bbox[2] - subtitle_bbox[0]
        subtitle_x = (self.image_width - subtitle_width) // 2
        subtitle_y = title_y + 90
        
        draw.text((subtitle_x, subtitle_y), subtitle_text, fill=accent_color, font=subtitle_font)
        
        # Description
        description_lines = [
            "Discover the most effective ESO builds from",
            "top-performing players. Explore meta builds",
            "for all trials."
        ]
        
        description_y = subtitle_y + 80
        for i, line in enumerate(description_lines):
            line_bbox = draw.textbbox((0, 0), line, font=description_font)
            line_width = line_bbox[2] - line_bbox[0]
            line_x = (self.image_width - line_width) // 2
            draw.text((line_x, description_y + (i * 40)), line, fill='#e8e8e8', font=description_font)
        
        # Add ESO-style decorative elements
        self._corner_icons = []  # Reset corner icons
        self._draw_decorative_elements(draw, primary_color, accent_color)
        
        # Paste ability icons on top
        for icon, position in self._corner_icons:
            img.paste(icon, position, icon if icon.mode == 'RGBA' else None)
        
        # Save image with optimization
        filename = "social-preview-dev.png" if is_develop else "social-preview.png"
        output_path = self.static_dir / filename
        
        # Optimize for smaller file size while maintaining quality
        img = img.convert('P', palette=Image.ADAPTIVE, colors=256)
        img.save(output_path, "PNG", optimize=True, compress_level=9)
        
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
        # Create image with site banner background
        img = self._create_background_with_banner()
        draw = ImageDraw.Draw(img)
        
        # Color scheme for decorative elements
        if is_develop:
            primary_color = '#f39c12'
            secondary_color = '#e67e22'
            accent_color = '#f1c40f'
        else:
            primary_color = '#11998e'
            secondary_color = '#38ef7d'
            accent_color = '#a8edea'
        
        # Try to load fonts - increased sizes for readability
        try:
            title_font = ImageFont.truetype("/System/Library/Fonts/Arial Bold.ttf", 96)
            subtitle_font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 48)
        except (OSError, IOError):
            try:
                title_font = ImageFont.truetype("arial.ttf", 96)
                subtitle_font = ImageFont.truetype("arial.ttf", 48)
            except (OSError, IOError):
                title_font = ImageFont.load_default()
                subtitle_font = ImageFont.load_default()
        
        # Simplified title: just "esobuild.com"
        title_text = "esobuild.com"
        title_bbox = draw.textbbox((0, 0), title_text, font=title_font)
        title_width = title_bbox[2] - title_bbox[0]
        title_x = (self.image_width - title_width) // 2
        title_y = 200
        
        # Draw title with strong shadow for readability
        draw.text((title_x + 4, title_y + 4), title_text, fill='#000000', font=title_font)
        draw.text((title_x, title_y), title_text, fill='#ffffff', font=title_font)
        
        # Subtitle: "Build Page"
        subtitle_text = "Build Page"
        subtitle_bbox = draw.textbbox((0, 0), subtitle_text, font=subtitle_font)
        subtitle_width = subtitle_bbox[2] - subtitle_bbox[0]
        subtitle_x = (self.image_width - subtitle_width) // 2
        subtitle_y = title_y + 110
        
        # Draw subtitle with shadow
        draw.text((subtitle_x + 3, subtitle_y + 3), subtitle_text, fill='#000000', font=subtitle_font)
        draw.text((subtitle_x, subtitle_y), subtitle_text, fill=accent_color, font=subtitle_font)
        
        # Add decorative elements
        self._corner_icons = []  # Reset corner icons
        self._draw_decorative_elements(draw, primary_color, accent_color)
        
        # Paste ability icons on top
        for icon, position in self._corner_icons:
            img.paste(icon, position, icon if icon.mode == 'RGBA' else None)
        
        # Save image with optimization
        filename = f"social-preview-build-dev.png" if is_develop else "social-preview-build.png"
        output_path = self.static_dir / filename
        
        # Optimize for smaller file size while maintaining quality
        img = img.convert('P', palette=Image.ADAPTIVE, colors=256)
        img.save(output_path, "PNG", optimize=True, compress_level=9)
        
        logger.info(f"Generated build preview image: {output_path}")
        return output_path
    
    def create_trial_preview(self, trial_name: str, is_develop: bool = False) -> Path:
        """
        Create a preview image for a specific trial.
        
        Args:
            trial_name: Name of the trial
            is_develop: Whether this is for development environment
            
        Returns:
            Path to the generated image
        """
        # Create image with trial-specific background
        img = self._create_background_with_trial(trial_name)
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
        
        # Try to load fonts - increased sizes for readability over backgrounds
        try:
            title_font = ImageFont.truetype("/System/Library/Fonts/Arial Bold.ttf", 96)
            subtitle_font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 48)
            description_font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 36)
        except (OSError, IOError):
            try:
                title_font = ImageFont.truetype("arial.ttf", 96)
                subtitle_font = ImageFont.truetype("arial.ttf", 48)
                description_font = ImageFont.truetype("arial.ttf", 36)
            except (OSError, IOError):
                title_font = ImageFont.load_default()
                subtitle_font = ImageFont.load_default()
                description_font = ImageFont.load_default()
        
        # Trial title
        title_text = trial_name
        title_bbox = draw.textbbox((0, 0), title_text, font=title_font)
        title_width = title_bbox[2] - title_bbox[0]
        title_x = (self.image_width - title_width) // 2
        title_y = 180
        
        # Draw title with shadow effect
        draw.text((title_x + 3, title_y + 3), title_text, fill='#000000', font=title_font)
        draw.text((title_x, title_y), title_text, fill='#ffffff', font=title_font)
        
        # Subtitle
        subtitle_text = "ESOBuild.com"
        if is_develop:
            subtitle_text += " [DEV]"
        subtitle_bbox = draw.textbbox((0, 0), subtitle_text, font=subtitle_font)
        subtitle_width = subtitle_bbox[2] - subtitle_bbox[0]
        subtitle_x = (self.image_width - subtitle_width) // 2
        subtitle_y = title_y + 90
        
        draw.text((subtitle_x, subtitle_y), subtitle_text, fill=accent_color, font=subtitle_font)
        
        # Description
        description_lines = [
            "Explore meta builds and top performers",
            "for this trial on ESOBuild.com"
        ]
        
        description_y = subtitle_y + 80
        for i, line in enumerate(description_lines):
            line_bbox = draw.textbbox((0, 0), line, font=description_font)
            line_width = line_bbox[2] - line_bbox[0]
            line_x = (self.image_width - line_width) // 2
            draw.text((line_x, description_y + (i * 40)), line, fill='#e8e8e8', font=description_font)
        
        # Add decorative elements
        self._corner_icons = []  # Reset corner icons
        self._draw_decorative_elements(draw, primary_color, accent_color)
        
        # Paste ability icons on top
        for icon, position in self._corner_icons:
            img.paste(icon, position, icon if icon.mode == 'RGBA' else None)
        
        # Save image with optimization
        trial_slug = trial_name.lower().replace(' ', '').replace('-', '')
        filename = f"social-preview-{trial_slug}-dev.png" if is_develop else f"social-preview-{trial_slug}.png"
        output_path = self.static_dir / filename
        
        # Optimize for smaller file size while maintaining quality
        img = img.convert('P', palette=Image.ADAPTIVE, colors=256)
        img.save(output_path, "PNG", optimize=True, compress_level=9)
        
        logger.info(f"Generated trial preview image: {output_path}")
        return output_path
    
    def _create_background_with_banner(self) -> Image.Image:
        """Create background using the site banner."""
        # Start with dark background
        img = Image.new('RGB', (self.image_width, self.image_height), color='#1a1a2e')
        
        # Try to load site banner
        banner_path = self.static_dir / "banners" / "site_banner.png"
        if banner_path.exists():
            try:
                banner = Image.open(banner_path)
                # Resize banner to fit width, maintaining aspect ratio
                banner_width = self.image_width
                banner_height = int(banner_width * banner.height / banner.width)
                
                if banner_height < self.image_height:
                    # If banner is shorter than needed, crop from center
                    banner = banner.resize((banner_width, banner_height), Image.Resampling.LANCZOS)
                    # Create overlay for the full height
                    overlay = Image.new('RGB', (self.image_width, self.image_height), color='#1a1a2e')
                    # Paste banner in the center
                    paste_y = (self.image_height - banner_height) // 2
                    overlay.paste(banner, (0, paste_y))
                    banner = overlay
                else:
                    # If banner is taller, resize to fit height
                    banner = banner.resize((banner_width, self.image_height), Image.Resampling.LANCZOS)
                
                # Apply alpha blend (35% opacity)
                banner = banner.convert('RGBA')
                banner.putalpha(int(255 * 0.35))
                
                # Create overlay
                overlay = Image.new('RGBA', (self.image_width, self.image_height), (0, 0, 0, 0))
                overlay.paste(banner, (0, 0), banner)
                
                # Convert back to RGB
                img = Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')
                
            except Exception as e:
                logger.warning(f"Failed to load site banner: {e}")
        
        return img
    
    def _create_background_with_trial(self, trial_name: str) -> Image.Image:
        """Create background using trial-specific graphics."""
        # Start with dark background
        img = Image.new('RGB', (self.image_width, self.image_height), color='#1a1a2e')
        
        # Map trial name to image filename
        trial_mapping = {
            'Aetherian Archive': 'aetherianarchive',
            'Hel Ra Citadel': 'helracitadel',
            'Sanctum Ophidia': 'sanctumophidia',
            'Maw of Lorkhaj': 'maw_of_lorkaj',
            'The Halls of Fabrication': 'hallsoffabrication',
            'Asylum Sanctorium': 'asylumsanctorium',
            'Cloudrest': 'cloudrest',
            'Sunspire': 'sunspire',
            'Kyne\'s Aegis': 'kynesaegis',
            'Rockgrove': 'rockgrove',
            'Dreadsail Reef': 'dreadsail_reef',
            'Sanity\'s Edge': 'sanitysedge',
            'Lucent Citadel': 'lucentcitadel',
            'Ossein Cage': 'ossein_cage'
        }
        
        trial_slug = trial_mapping.get(trial_name, trial_name.lower().replace(' ', '').replace('-', '').replace('\'', ''))
        trial_bg_path = self.static_dir / "social-backgrounds" / f"{trial_slug}.png"
        
        if trial_bg_path.exists():
            try:
                trial_bg = Image.open(trial_bg_path)
                # Resize to fit social media dimensions
                trial_bg = trial_bg.resize((self.image_width, self.image_height), Image.Resampling.LANCZOS)
                
                # Apply alpha blend (30% opacity)
                trial_bg = trial_bg.convert('RGBA')
                trial_bg.putalpha(int(255 * 0.3))
                
                # Create overlay
                overlay = Image.new('RGBA', (self.image_width, self.image_height), (0, 0, 0, 0))
                overlay.paste(trial_bg, (0, 0), trial_bg)
                
                # Convert back to RGB
                img = Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')
                
            except Exception as e:
                logger.warning(f"Failed to load trial background for {trial_name}: {e}")
        
        return img
    
    def _draw_gradient_background(self, draw: ImageDraw.Draw, color1: str, color2: str):
        """Draw a rich multi-stop gradient background with depth."""
        # Create a 3-color gradient for more depth
        # Dark base -> color1 -> color2
        base_color = '#0a0a1e'
        
        r_base, g_base, b_base = self._hex_to_rgb(base_color)
        r1, g1, b1 = self._hex_to_rgb(color1)
        r2, g2, b2 = self._hex_to_rgb(color2)
        
        for y in range(self.image_height):
            # Create a smooth 3-stop gradient
            ratio = y / self.image_height
            
            if ratio < 0.3:
                # Base to color1
                local_ratio = ratio / 0.3
                r = int(r_base + (r1 - r_base) * local_ratio)
                g = int(g_base + (g1 - g_base) * local_ratio)
                b = int(b_base + (b1 - b_base) * local_ratio)
            else:
                # color1 to color2
                local_ratio = (ratio - 0.3) / 0.7
                r = int(r1 + (r2 - r1) * local_ratio)
                g = int(g1 + (g2 - g1) * local_ratio)
                b = int(b1 + (b2 - b1) * local_ratio)
            
            # Add horizontal variation for depth
            for x in range(self.image_width):
                # Subtle left-right gradient overlay
                horizontal_factor = (x / self.image_width - 0.5) * 0.15
                
                final_r = max(0, min(255, int(r * (1 + horizontal_factor))))
                final_g = max(0, min(255, int(g * (1 + horizontal_factor))))
                final_b = max(0, min(255, int(b * (1 + horizontal_factor))))
                
                draw.point((x, y), fill=(final_r, final_g, final_b))
    
    def _draw_decorative_elements(self, draw: ImageDraw.Draw, primary_color: str, accent_color: str):
        """Add decorative elements to the image including ability icons."""
        # Add ESO ability icons in the corners
        icons_dir = Path("static/icons")
        if icons_dir.exists():
            # Select some iconic ESO ability icons (using existing files)
            icon_files = [
                "ability_dragonknight_006_b.png",     # Dragon Knight fire - top left
                "ability_sorcerer_crushing_winds.png", # Sorcerer lightning - top right
                "ability_nightblade_005_b.png",       # Nightblade shadow - bottom left
                "ability_sorcerer_critical_surge.png" # Sorcerer power - bottom right
            ]
            
            icon_size = 80
            icon_positions = [
                (40, 40),                                          # Top left
                (self.image_width - icon_size - 40, 40),          # Top right
                (40, self.image_height - icon_size - 40),         # Bottom left
                (self.image_width - icon_size - 40, 
                 self.image_height - icon_size - 40)              # Bottom right
            ]
            
            for icon_file, position in zip(icon_files, icon_positions):
                icon_path = icons_dir / icon_file
                if icon_path.exists():
                    try:
                        # Load and resize icon
                        icon = Image.open(icon_path)
                        icon = icon.resize((icon_size, icon_size), Image.Resampling.LANCZOS)
                        
                        # Add a subtle glow effect behind the icon
                        glow_size = icon_size + 10
                        glow_pos = (position[0] - 5, position[1] - 5)
                        draw.ellipse([glow_pos[0], glow_pos[1], 
                                    glow_pos[0] + glow_size, glow_pos[1] + glow_size],
                                   fill=None, outline=accent_color, width=2)
                        
                        # Paste icon (need to create base image reference)
                        # We'll store the image reference to paste later
                        if not hasattr(self, '_corner_icons'):
                            self._corner_icons = []
                        self._corner_icons.append((icon, position))
                        
                    except Exception as e:
                        logger.warning(f"Failed to load icon {icon_file}: {e}")
        
        # Add decorative circles around where icons will be
        for x, y in [(100, 100), (self.image_width - 100, 100), 
                     (100, self.image_height - 100), (self.image_width - 100, self.image_height - 100)]:
            draw.ellipse([x - 50, y - 50, x + 50, y + 50], outline=accent_color, width=2)
        
        # Add connecting lines
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

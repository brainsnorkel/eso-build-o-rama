"""
Static Page Generator Module
Generates HTML pages for build displays.
"""

import logging
from typing import List, Dict, Optional
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape
from datetime import datetime

from .models import CommonBuild, PlayerBuild, TrialReport

logger = logging.getLogger(__name__)


class PageGenerator:
    """Generates static HTML pages for builds."""
    
    def __init__(self, template_dir: str = "templates", output_dir: str = "output"):
        """
        Initialize the page generator.
        
        Args:
            template_dir: Directory containing Jinja2 templates
            output_dir: Directory for generated HTML files
        """
        self.template_dir = Path(template_dir)
        self.output_dir = Path(output_dir)
        
        # Create output directory if it doesn't exist
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize Jinja2 environment
        self.env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=select_autoescape(['html', 'xml'])
        )
        
        # Add custom filters
        self.env.filters['format_dps'] = self._format_dps
        self.env.filters['format_percentage'] = self._format_percentage
        
        logger.info(f"Page generator initialized (templates: {template_dir}, output: {output_dir})")
    
    def generate_build_page(
        self,
        build: CommonBuild,
        update_version: str
    ) -> str:
        """
        Generate a single build page.
        
        Args:
            build: CommonBuild object
            update_version: Game update version (e.g., 'U48')
            
        Returns:
            Path to generated HTML file
        """
        logger.info(f"Generating build page: {build.build_slug}")
        
        # Load template
        template = self.env.get_template('build_page.html')
        
        # Prepare data for template
        context = {
            'build': build,
            'update_version': update_version,
            'best_player': build.best_player,
            'generated_date': datetime.now().strftime('%Y-%m-%d'),
            'page_title': self._get_page_title(build),
            'meta_description': self._get_meta_description(build)
        }
        
        # Render template
        html = template.render(**context)
        
        # Generate filename
        filename = f"{update_version.lower()}-{build.build_slug}.html"
        filepath = self.output_dir / filename
        
        # Write file
        filepath.write_text(html, encoding='utf-8')
        
        logger.info(f"Generated: {filepath}")
        return str(filepath)
    
    def generate_index_page(
        self,
        all_builds: List[CommonBuild],
        update_version: str
    ) -> str:
        """
        Generate the index page listing all builds.
        
        Args:
            all_builds: List of all common builds
            update_version: Game update version
            
        Returns:
            Path to generated HTML file
        """
        logger.info(f"Generating index page with {len(all_builds)} builds")
        
        # Group builds by trial and boss
        builds_by_trial = self._group_builds_by_trial(all_builds)
        
        # Load template
        template = self.env.get_template('index_page.html')
        
        # Prepare data
        context = {
            'builds_by_trial': builds_by_trial,
            'update_version': update_version,
            'total_builds': len(all_builds),
            'generated_date': datetime.now().strftime('%Y-%m-%d %H:%M'),
            'page_title': f'ESO Build-O-Rama - Top Builds for {update_version}',
            'meta_description': f'Top performing Elder Scrolls Online trial builds for {update_version}'
        }
        
        # Render template
        html = template.render(**context)
        
        # Write file
        filepath = self.output_dir / 'index.html'
        filepath.write_text(html, encoding='utf-8')
        
        logger.info(f"Generated index: {filepath}")
        return str(filepath)
    
    def generate_all_pages(
        self,
        all_builds: List[CommonBuild],
        update_version: str
    ) -> Dict[str, str]:
        """
        Generate all build pages and index.
        
        Args:
            all_builds: List of all common builds
            update_version: Game update version
            
        Returns:
            Dictionary mapping build slugs to file paths
        """
        logger.info(f"Generating all pages for {len(all_builds)} builds")
        
        generated_files = {}
        
        # Generate index page
        index_path = self.generate_index_page(all_builds, update_version)
        generated_files['index'] = index_path
        
        # Generate individual build pages
        for build in all_builds:
            try:
                filepath = self.generate_build_page(build, update_version)
                generated_files[build.build_slug] = filepath
            except Exception as e:
                logger.error(f"Error generating page for {build.build_slug}: {e}")
                continue
        
        logger.info(f"Generated {len(generated_files)} pages")
        return generated_files
    
    def _group_builds_by_trial(
        self,
        builds: List[CommonBuild]
    ) -> Dict[str, Dict[str, List[CommonBuild]]]:
        """Group builds by trial and boss."""
        grouped = {}
        
        for build in builds:
            trial = build.trial_name
            boss = build.boss_name
            
            if trial not in grouped:
                grouped[trial] = {}
            
            if boss not in grouped[trial]:
                grouped[trial][boss] = []
            
            grouped[trial][boss].append(build)
        
        return grouped
    
    def _get_page_title(self, build: CommonBuild) -> str:
        """Generate page title for a build."""
        display_name = build.get_display_name()
        sets = ' / '.join(build.sets) if build.sets else 'Unknown Sets'
        return f"{display_name} - {sets} | ESO Build-O-Rama"
    
    def _get_meta_description(self, build: CommonBuild) -> str:
        """Generate meta description for a build."""
        display_name = build.get_display_name()
        sets = ' / '.join(build.sets) if build.sets else 'Unknown Sets'
        trial = build.trial_name
        boss = build.boss_name
        
        return (
            f"Top performing {display_name} build with {sets} "
            f"from {trial} - {boss}. Featuring {build.count} top players."
        )
    
    @staticmethod
    def _format_dps(value: float) -> str:
        """Format DPS value for display."""
        if value >= 1_000_000:
            return f"{value / 1_000_000:.2f}M"
        elif value >= 1_000:
            return f"{value / 1_000:.1f}K"
        else:
            return f"{int(value)}"
    
    @staticmethod
    def _format_percentage(value: float) -> str:
        """Format percentage value for display."""
        return f"{value:.1f}%"

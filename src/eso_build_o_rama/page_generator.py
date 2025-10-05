"""
Static Page Generator Module
Generates HTML pages for build displays.
"""

import logging
import json
from typing import List, Dict, Optional, Any
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
        
        # Load boss order from trial_bosses.json
        self.boss_order = self._load_boss_order()
        
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
        self.env.filters['format_timestamp'] = self._format_timestamp
        
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
        trial_slug = build.trial_name.lower().replace(' ', '-')
        context = {
            'build': build,
            'update_version': update_version,
            'best_player': build.best_player,
            'trial_slug': trial_slug,
            'generated_date': datetime.now().strftime('%Y-%m-%d'),
            'page_title': self._get_page_title(build),
            'meta_description': self._get_meta_description(build)
        }
        
        # Debug: Check DPS value being passed to template
        if build.best_player:
            logger.debug(f"Passing to template - Best player: {build.best_player.character_name}, DPS: {build.best_player.dps:,}")
        
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
        update_version: str,
        trials_metadata: Optional[Dict[str, Dict[str, Any]]] = None
    ) -> str:
        """
        Generate the index page listing all builds.
        
        Args:
            all_builds: List of all common builds
            update_version: Game update version
            trials_metadata: Optional metadata about trials including last updated times
            
        Returns:
            Path to generated HTML file
        """
        logger.info(f"Generating index page with {len(all_builds)} builds")
        
        # Group builds by trial and boss
        builds_by_trial = self._group_builds_by_trial(all_builds)
        
        # Load template
        template = self.env.get_template('index_page.html')
        
        # Add timestamp information to each trial
        builds_by_trial_with_timestamps = {}
        for trial_name, bosses_data in builds_by_trial.items():
            builds_by_trial_with_timestamps[trial_name] = {
                'bosses': bosses_data,
                'metadata': trials_metadata.get(trial_name, {}) if trials_metadata else {}
            }
        
        # Prepare data
        context = {
            'builds_by_trial': builds_by_trial_with_timestamps,
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
    
    def generate_home_page(
        self,
        builds_by_trial: Dict[str, Dict[str, Dict[str, Any]]]
    ) -> str:
        """
        Generate the home page listing all trials.
        
        Args:
            builds_by_trial: Dictionary of {trial_name: {boss_name: {'builds': [builds], 'total_reports': int}}}
            
        Returns:
            Path to generated HTML file
        """
        logger.info("Generating home page")
        
        # Prepare trial data with top build for each trial
        trials = []
        for trial_name, bosses in builds_by_trial.items():
            # Find the highest DPS build across all bosses in this trial
            all_builds = []
            for boss_data in bosses.values():
                if isinstance(boss_data, dict) and 'builds' in boss_data:
                    all_builds.extend(boss_data['builds'])
                elif isinstance(boss_data, list):
                    all_builds.extend(boss_data)
            
            if all_builds:
                top_build = max(all_builds, key=lambda b: b.best_player.dps if b.best_player else 0)
            else:
                top_build = None
            
            trial_slug = trial_name.lower().replace(' ', '-')
            trials.append({
                'name': trial_name,
                'slug': trial_slug,
                'top_build': top_build
            })
        
        # Sort trials alphabetically
        trials.sort(key=lambda t: t['name'])
        
        # Load template
        template = self.env.get_template('home.html')
        
        # Render template
        context = {
            'trials': trials,
            'generated_date': datetime.now().strftime('%Y-%m-%d')
        }
        html = template.render(**context)
        
        # Write file
        filepath = self.output_dir / 'index.html'
        filepath.write_text(html, encoding='utf-8')
        
        logger.info(f"Generated home page: {filepath}")
        return str(filepath)
    
    def generate_trial_page(
        self,
        trial_name: str,
        bosses: Dict[str, List[CommonBuild]]
    ) -> str:
        """
        Generate a trial page with all bosses and their builds.
        
        Args:
            trial_name: Name of the trial
            bosses: Dictionary of {boss_name: [builds]}
            
        Returns:
            Path to generated HTML file
        """
        logger.info(f"Generating trial page for {trial_name}")
        
        # Sort builds for each boss by popularity (count) then DPS
        sorted_bosses = {}
        for boss_name, builds in bosses.items():
            sorted_builds = sorted(
                builds,
                key=lambda b: (-b.count, -(b.best_player.dps if b.best_player else 0))
            )
            sorted_bosses[boss_name] = sorted_builds
        
        # Load template
        template = self.env.get_template('trial.html')
        
        # Render template
        context = {
            'trial_name': trial_name,
            'bosses': sorted_bosses,
            'generated_date': datetime.now().strftime('%Y-%m-%d')
        }
        html = template.render(**context)
        
        # Write file
        trial_slug = trial_name.lower().replace(' ', '-')
        filepath = self.output_dir / f'{trial_slug}.html'
        filepath.write_text(html, encoding='utf-8')
        
        logger.info(f"Generated trial page: {filepath}")
        return str(filepath)
    
    def generate_all_pages(
        self,
        all_builds: List[CommonBuild],
        update_version: str,
        trials_metadata: Optional[Dict[str, Dict[str, Any]]] = None
    ) -> Dict[str, str]:
        """
        Generate all build pages and index.
        
        Args:
            all_builds: List of all common builds
            update_version: Game update version
            trials_metadata: Optional metadata about trials including last updated times
            
        Returns:
            Dictionary mapping build slugs to file paths
        """
        logger.info(f"Generating all pages for {len(all_builds)} builds")
        
        generated_files = {}
        
        # Group builds by trial for proper site structure
        builds_by_trial = self._group_builds_by_trial(all_builds)
        
        # Generate home page (index.html) with trial links
        home_path = self.generate_home_page(builds_by_trial)
        generated_files['home'] = home_path
        
        # Generate individual trial pages
        for trial_name, trial_data in builds_by_trial.items():
            # Extract just the bosses data for trial page generation
            bosses_data = {boss: data['builds'] for boss, data in trial_data.items()}
            trial_path = self.generate_trial_page(trial_name, bosses_data)
            generated_files[f'trial_{trial_name.lower().replace(" ", "_")}'] = trial_path
        
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
    
    def _load_boss_order(self) -> Dict[str, List[str]]:
        """Load boss order from trial_bosses.json."""
        bosses_file = Path(__file__).parent.parent.parent / "data" / "trial_bosses.json"
        try:
            with open(bosses_file, 'r') as f:
                data = json.load(f)
                return data.get('trial_bosses', {})
        except FileNotFoundError:
            logger.warning(f"trial_bosses.json not found at {bosses_file}")
            return {}
        except json.JSONDecodeError:
            logger.warning(f"Could not parse trial_bosses.json")
            return {}
    
    def _group_builds_by_trial(
        self,
        builds: List[CommonBuild]
    ) -> Dict[str, Dict[str, Dict[str, Any]]]:
        """Group builds by trial and boss with additional metadata, preserving boss order from trial_bosses.json."""
        grouped = {}
        
        # First, collect all builds
        for build in builds:
            trial = build.trial_name
            boss = build.boss_name
            
            if trial not in grouped:
                grouped[trial] = {}
            
            if boss not in grouped[trial]:
                grouped[trial][boss] = {
                    'builds': [],
                    'total_reports': 0
                }
            
            grouped[trial][boss]['builds'].append(build)
            
            # Track the highest report count for this boss (should be the same for all builds of same boss)
            if build.report_count > grouped[trial][boss]['total_reports']:
                grouped[trial][boss]['total_reports'] = build.report_count
        
        # Now reorder bosses according to trial_bosses.json
        ordered_grouped = {}
        for trial, bosses_data in grouped.items():
            if trial in self.boss_order:
                # Create ordered dict based on trial_bosses.json order
                ordered_grouped[trial] = {}
                for boss_name in self.boss_order[trial]:
                    if boss_name in bosses_data:
                        ordered_grouped[trial][boss_name] = bosses_data[boss_name]
                
                # Add any bosses not in the order file (shouldn't happen, but just in case)
                for boss_name, data in bosses_data.items():
                    if boss_name not in ordered_grouped[trial]:
                        ordered_grouped[trial][boss_name] = data
            else:
                # Trial not in boss_order, keep original order
                ordered_grouped[trial] = bosses_data
        
        return ordered_grouped
    
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
    
    @staticmethod
    def _format_timestamp(timestamp_str: str) -> str:
        """Format timestamp for display."""
        if not timestamp_str:
            return "Never"
        
        try:
            from datetime import datetime
            # Parse ISO format timestamp
            dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            return dt.strftime('%Y-%m-%d %H:%M UTC')
        except (ValueError, TypeError):
            return timestamp_str

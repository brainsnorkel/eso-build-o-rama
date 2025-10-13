"""
Static Page Generator Module
Generates HTML pages for build displays.
"""

import logging
import json
import shutil
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
        
        # Detect if this is development mode based on output directory
        self.is_develop = 'dev' in str(output_dir).lower()
        
        # Load boss order from trial_bosses.json
        self.boss_order = self._load_boss_order()
        
        # Create output directory if it doesn't exist
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy static assets to output directory
        self._copy_static_assets()
        
        # Initialize Jinja2 environment
        self.env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=select_autoescape(['html', 'xml'])
        )
        
        # Add custom filters
        self.env.filters['format_dps'] = self._format_dps
        self.env.filters['format_metric'] = self._format_metric
        self.env.filters['format_percentage'] = self._format_percentage
        self.env.filters['format_timestamp'] = self._format_timestamp
        self.env.filters['eso_hub_set_url'] = self._eso_hub_set_url
        self.env.filters['eso_hub_ability_url'] = self._eso_hub_ability_url
        self.env.filters['eso_hub_mundus_url'] = self._eso_hub_mundus_url
        self.env.filters['trial_background_image'] = self._trial_background_image
        self.env.filters['trial_social_image'] = self._trial_social_image
        
        logger.info(f"Page generator initialized (templates: {template_dir}, output: {output_dir})")
    
    def generate_build_page(
        self,
        build: CommonBuild,
        update_version: str,
        app_version: str = "1.0.0"
    ) -> str:
        """
        Generate a single build page.
        
        Args:
            build: CommonBuild object
            update_version: Game update version (e.g., 'U48')
            app_version: Application version for display
            
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
            'generated_date': datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
            'page_title': self._get_page_title(build),
            'meta_description': self._get_meta_description(build),
            'is_develop': self.is_develop,
            'social_image_url': self._get_social_image_url('build', None, app_version),
            'app_version': app_version
        }
        
        # Debug: Check DPS value being passed to template
        if build.best_player:
            logger.debug(f"Passing to template - Best player: {build.best_player.character_name}, DPS: {build.best_player.dps:,}")
        
        # Render template
        html = template.render(**context)
        
        # Generate filename with trial and boss (no version prefix)
        trial_slug = build.trial_name.lower().replace(' ', '-').replace("'", "")
        boss_slug = build.boss_name.lower().replace(' ', '-').replace("'", "").replace('&', 'and').replace('/', '-')
        filename = f"{trial_slug}-{boss_slug}-{build.build_slug}.html"
        filepath = self.output_dir / filename
        
        # Write file
        filepath.write_text(html, encoding='utf-8')
        
        logger.info(f"Generated: {filepath}")
        return str(filepath)
    
    def generate_home_page(
        self,
        builds_by_trial: Dict[str, Dict[str, Dict[str, Any]]],
        trials_metadata: Optional[Dict[str, Dict[str, Any]]] = None,
        app_version: str = "1.0.0",
        aggregated_builds: Optional[Dict[str, List[CommonBuild]]] = None
    ) -> str:
        """
        Generate the home page listing all trials.
        
        Args:
            builds_by_trial: Dictionary of {trial_name: {boss_name: {'builds': [builds], 'total_reports': int}}}
            trials_metadata: Optional metadata about trials including cache stats
            app_version: Application version for display
            aggregated_builds: Optional aggregated builds data for TL;DR card
            
        Returns:
            Path to generated HTML file
        """
        logger.info("Generating home page")
        
        # Load trial data to get trial IDs
        import json
        trials_file = self.output_dir.parent / 'data' / 'trials.json'
        with open(trials_file, 'r') as f:
            trial_data = json.load(f)
        
        # Create a mapping of trial name to ID
        trial_id_map = {trial['name']: trial['id'] for trial in trial_data['trials']}
        
        # Prepare trial data with top build for each trial
        trials = []
        for trial_name, bosses in builds_by_trial.items():
            # Find the highest DPS build across all bosses in this trial (DPS role only)
            all_builds = []
            for boss_data in bosses.values():
                if isinstance(boss_data, dict) and 'builds' in boss_data:
                    all_builds.extend(boss_data['builds'])
                elif isinstance(boss_data, list):
                    all_builds.extend(boss_data)
            
            # Filter for DPS role builds only (exclude tanks and healers)
            dps_builds = [b for b in all_builds if b.best_player and b.best_player.role == 'dps']
            
            if dps_builds:
                top_build = max(dps_builds, key=lambda b: b.best_player.dps)
            else:
                top_build = None
            
            trial_slug = trial_name.lower().replace(' ', '-')
            trial_id = trial_id_map.get(trial_name, 0)  # Default to 0 if not found
            
            # Get last updated time from trials_metadata
            last_updated = None
            if trials_metadata and trial_name in trials_metadata:
                last_updated = trials_metadata[trial_name].get('last_updated')
            
            trials.append({
                'name': trial_name,
                'slug': trial_slug,
                'top_build': top_build,
                'id': trial_id,
                'last_updated': last_updated,
            })
        
        # Sort trials by trial ID in descending order (newest trials first)
        trials.sort(key=lambda t: t['id'], reverse=True)
        
        # Load template
        template = self.env.get_template('home.html')
        
        # Render template
        context = {
            'trials': trials,
            'generated_date': datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
            'is_develop': self.is_develop,
            'social_image_url': self._get_social_image_url('home', None, app_version),
            'app_version': app_version,
            'aggregated_builds': aggregated_builds
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
        bosses: Dict[str, List[CommonBuild]],
        app_version: str = "1.0.0"
    ) -> str:
        """
        Generate a trial page with all bosses and their builds.
        
        Args:
            trial_name: Name of the trial
            bosses: Dictionary of {boss_name: [builds]}
            app_version: Application version for display
            
        Returns:
            Path to generated HTML file
        """
        logger.info(f"Generating trial page for {trial_name}")
        
        # Sort builds for each boss by role, then popularity (count) then DPS
        sorted_bosses = {}
        for boss_name, builds in bosses.items():
            # Define role order: DPS first, then Healer, then Tank
            role_order = {'dps': 0, 'healer': 1, 'tank': 2}
            
            sorted_builds = sorted(
                builds,
                key=lambda b: (
                    role_order.get(b.best_player.role.lower() if b.best_player else 'dps', 3),  # Role order (unknown roles last)
                    -b.count,  # Popularity (descending)
                    -(b.best_player.dps if b.best_player else 0)  # DPS (descending)
                )
            )
            sorted_bosses[boss_name] = sorted_builds
        
        # Load template
        template = self.env.get_template('trial.html')
        
        # Render template
        context = {
            'trial_name': trial_name,
            'bosses': sorted_bosses,
            'generated_date': datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
            'is_develop': self.is_develop,
            'social_image_url': self._get_social_image_url('trial', trial_name, app_version),
            'app_version': app_version
        }
        html = template.render(**context)
        
        # Write file
        trial_slug = trial_name.lower().replace(' ', '-')
        filepath = self.output_dir / f'{trial_slug}.html'
        filepath.write_text(html, encoding='utf-8')
        
        logger.info(f"Generated trial page: {filepath}")
        return str(filepath)
    
    def generate_about_page(self, app_version: str = "1.0.0") -> str:
        """
        Generate the about page.
        
        Args:
            app_version: Application version for display
        
        Returns:
            Path to generated HTML file
        """
        logger.info("Generating about page")
        
        # Load template
        template = self.env.get_template('about.html')
        
        # Render template
        context = {
            'generated_date': datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
            'is_develop': self.is_develop,
            'app_version': app_version
        }
        html = template.render(**context)
        
        # Write file
        filepath = self.output_dir / 'about.html'
        filepath.write_text(html, encoding='utf-8')
        
        logger.info(f"Generated about page: {filepath}")
        return str(filepath)
    
    def generate_tldr_summary_page(self, aggregated_builds: Dict[str, List[CommonBuild]], app_version: str = "1.0.0") -> str:
        """
        Generate the TL;DR summary page showing top builds across all trials.
        
        Args:
            aggregated_builds: Dictionary mapping role names to lists of aggregated builds
            app_version: Application version for display
            
        Returns:
            Path to generated HTML file
        """
        logger.info("Generating TL;DR summary page")
        
        # Combine all builds into a single "All Encounters" section
        all_builds = []
        for role, builds in aggregated_builds.items():
            all_builds.extend(builds)
        
        # Sort by role (DPS first, then Healer, then Tank)
        role_order = {'dps': 0, 'healer': 1, 'tank': 2}
        all_builds.sort(key=lambda b: role_order.get(b.best_player.role.lower() if b.best_player else 'dps', 3))
        
        bosses = {"All Encounters": all_builds}
        
        # Load template
        template = self.env.get_template('trial.html')
        
        # Render template
        context = {
            'trial_name': "TL;DR: Top Builds",
            'bosses': bosses,
            'generated_date': datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
            'is_develop': self.is_develop,
            'social_image_url': self._get_social_image_url('trial', "TL;DR: Top Builds", app_version),
            'app_version': app_version,
            'hide_download_button': True  # Hide download button for TL;DR page
        }
        html = template.render(**context)
        
        # Write file
        filepath = self.output_dir / 'tldr-top-builds.html'
        filepath.write_text(html, encoding='utf-8')
        
        logger.info(f"Generated TL;DR summary page: {filepath}")
        return str(filepath)
    
    def generate_aggregated_build_page(self, build: CommonBuild, update_version: str, app_version: str = "1.0.0") -> str:
        """
        Generate an aggregated build page showing build data across all trials.
        
        Args:
            build: Aggregated CommonBuild object
            update_version: Game update version (e.g., 'U48')
            app_version: Application version for display
            
        Returns:
            Path to generated HTML file
        """
        logger.info(f"Generating aggregated build page: {build.build_slug}")
        
        # Load template
        template = self.env.get_template('build_page.html')
        
        # Prepare data for template
        context = {
            'build': build,
            'update_version': update_version,
            'best_player': build.best_player,
            'trial_slug': 'tldr-top-builds',
            'generated_date': datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
            'page_title': self._get_page_title(build),
            'meta_description': self._get_meta_description(build),
            'is_develop': self.is_develop,
            'social_image_url': self._get_social_image_url('build', None, app_version),
            'app_version': app_version,
            'trials_list': build.trials_appeared_in,  # Additional context for aggregated builds
            'is_aggregated': True
        }
        
        # Render template
        html = template.render(**context)
        
        # Generate filename
        filename = f"tldr-{build.build_slug}.html"
        filepath = self.output_dir / filename
        
        # Write file
        filepath.write_text(html, encoding='utf-8')
        
        logger.info(f"Generated aggregated build page: {filepath}")
        return str(filepath)
    
    def generate_all_pages(
        self,
        all_builds: List[CommonBuild],
        update_version: str,
        trials_metadata: Optional[Dict[str, Dict[str, Any]]] = None,
        app_version: str = "1.0.0",
        aggregated_builds: Optional[Dict[str, List[CommonBuild]]] = None
    ) -> Dict[str, str]:
        """
        Generate all build pages and index.
        
        Args:
            all_builds: List of all common builds
            update_version: Game update version
            trials_metadata: Optional metadata about trials including last updated times
            app_version: Application version for display
            aggregated_builds: Optional aggregated builds data for TL;DR card
            
        Returns:
            Dictionary mapping build slugs to file paths
        """
        logger.info(f"Generating all pages for {len(all_builds)} builds")
        
        generated_files = {}
        
        # Group builds by trial for proper site structure
        builds_by_trial = self._group_builds_by_trial(all_builds)
        
        # Generate home page (index.html) with trial links
        home_path = self.generate_home_page(builds_by_trial, trials_metadata, app_version, aggregated_builds)
        generated_files['home'] = home_path
        
        # Generate about page
        about_path = self.generate_about_page(app_version)
        generated_files['about'] = about_path
        
        # Generate individual trial pages
        for trial_name, trial_data in builds_by_trial.items():
            # Extract just the bosses data for trial page generation
            bosses_data = {boss: data['builds'] for boss, data in trial_data.items()}
            trial_path = self.generate_trial_page(trial_name, bosses_data, app_version)
            generated_files[f'trial_{trial_name.lower().replace(" ", "_")}'] = trial_path
        
        # Generate individual build pages
        for build in all_builds:
            try:
                filepath = self.generate_build_page(build, update_version, app_version)
                generated_files[build.build_slug] = filepath
            except Exception as e:
                logger.error(f"Error generating page for {build.build_slug}: {e}")
                continue
        
        # Generate sitemap.xml
        sitemap_path = self.generate_sitemap(all_builds, builds_by_trial)
        generated_files['sitemap'] = sitemap_path
        
        # Generate robots.txt
        robots_path = self.generate_robots_txt()
        generated_files['robots'] = robots_path
        
        logger.info(f"Generated {len(generated_files)} pages")
        return generated_files
    
    def generate_sitemap(
        self,
        all_builds: List[CommonBuild],
        builds_by_trial: Dict[str, Dict[str, Dict[str, Any]]]
    ) -> str:
        """
        Generate sitemap.xml for search engine discovery.
        
        Args:
            all_builds: List of all common builds
            builds_by_trial: Grouped builds by trial
            
        Returns:
            Path to generated sitemap.xml file
        """
        logger.info("Generating sitemap.xml")
        
        # Determine base URL based on environment
        base_url = "https://brainsnorkel.github.io/eso-build-o-rama" if self.is_develop else "https://esobuild.com"
        
        # Start XML document
        xml_lines = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
        ]
        
        # Current timestamp for lastmod
        lastmod = datetime.utcnow().strftime('%Y-%m-%d')
        
        # Add home page
        xml_lines.extend([
            '  <url>',
            f'    <loc>{base_url}/index.html</loc>',
            f'    <lastmod>{lastmod}</lastmod>',
            '    <changefreq>daily</changefreq>',
            '    <priority>1.0</priority>',
            '  </url>',
        ])
        
        # Add about page
        xml_lines.extend([
            '  <url>',
            f'    <loc>{base_url}/about.html</loc>',
            f'    <lastmod>{lastmod}</lastmod>',
            '    <changefreq>monthly</changefreq>',
            '    <priority>0.5</priority>',
            '  </url>',
        ])
        
        # Add TL;DR summary page
        xml_lines.extend([
            '  <url>',
            f'    <loc>{base_url}/tldr-top-builds.html</loc>',
            f'    <lastmod>{lastmod}</lastmod>',
            '    <changefreq>daily</changefreq>',
            '    <priority>0.9</priority>',
            '  </url>',
        ])
        
        # Add trial pages
        for trial_name in builds_by_trial.keys():
            trial_slug = trial_name.lower().replace(' ', '-')
            xml_lines.extend([
                '  <url>',
                f'    <loc>{base_url}/{trial_slug}.html</loc>',
                f'    <lastmod>{lastmod}</lastmod>',
                '    <changefreq>weekly</changefreq>',
                '    <priority>0.8</priority>',
                '  </url>',
            ])
        
        # Add individual build pages
        for build in all_builds:
            trial_slug = build.trial_name.lower().replace(' ', '-').replace("'", "")
            boss_slug = build.boss_name.lower().replace(' ', '-').replace("'", "").replace('&', 'and').replace('/', '-')
            filename = f"{trial_slug}-{boss_slug}-{build.build_slug}.html"
            
            xml_lines.extend([
                '  <url>',
                f'    <loc>{base_url}/{filename}</loc>',
                f'    <lastmod>{lastmod}</lastmod>',
                '    <changefreq>weekly</changefreq>',
                '    <priority>0.6</priority>',
                '  </url>',
            ])
        
        # Close XML document
        xml_lines.append('</urlset>')
        
        # Write sitemap
        sitemap_content = '\n'.join(xml_lines)
        filepath = self.output_dir / 'sitemap.xml'
        filepath.write_text(sitemap_content, encoding='utf-8')
        
        logger.info(f"Generated sitemap.xml with {len(all_builds) + len(builds_by_trial) + 1} URLs: {filepath}")
        return str(filepath)
    
    def generate_robots_txt(self) -> str:
        """
        Generate robots.txt for search engine crawlers.
        
        Returns:
            Path to generated robots.txt file
        """
        logger.info("Generating robots.txt")
        
        # Determine base URL based on environment
        base_url = "https://brainsnorkel.github.io/eso-build-o-rama" if self.is_develop else "https://esobuild.com"
        
        robots_content = f"""# robots.txt for ESOBuild.com
User-agent: *
Allow: /

# Sitemap location
Sitemap: {base_url}/sitemap.xml

# Disallow cache directory (if exposed)
Disallow: /cache/
"""
        
        filepath = self.output_dir / 'robots.txt'
        filepath.write_text(robots_content, encoding='utf-8')
        
        logger.info(f"Generated robots.txt: {filepath}")
        return str(filepath)
    
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
    
    def _copy_static_assets(self):
        """Copy static assets to output directory."""
        static_source = Path(__file__).parent.parent.parent / "static"
        static_dest = self.output_dir / "static"
        
        if static_source.exists():
            # Remove existing static dir to ensure fresh copy
            if static_dest.exists():
                shutil.rmtree(static_dest)
            
            # Copy static directory
            shutil.copytree(static_source, static_dest)
            logger.debug(f"Copied static assets to {static_dest}")
        else:
            logger.warning(f"Static assets directory not found: {static_source}")
    
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
    
    def _get_social_image_url(self, page_type: str = 'home', trial_name: str = None, app_version: str = "1.0.0") -> str:
        """Get the URL for social media preview images."""
        # Social media crawlers need absolute URLs
        # Always use esobuild.com domain for social previews (works for both dev and prod)
        base_url = "https://esobuild.com/"
        
        # Discord ignores query parameters, so we use versioned filenames (b2, b3, etc)
        # Plus add query param with major.minor version for other crawlers
        # Extract major.minor from app_version (e.g., "1.2.5" -> "1.2")
        try:
            version_parts = app_version.split('.')
            major_minor = f"{version_parts[0]}.{version_parts[1]}" if len(version_parts) >= 2 else app_version
        except:
            major_minor = "1.0"
        
        # Current image version suffix (increment when images change: b2, b3, b4, etc)
        image_version = "b2"
        
        if page_type == 'trial' and trial_name:
            # Use trial-specific social preview
            trial_slug = trial_name.lower().replace(' ', '').replace('-', '').replace('\'', '')
            filename = f"social-preview-{trial_slug}-dev-{image_version}.png" if self.is_develop else f"social-preview-{trial_slug}-{image_version}.png"
        elif page_type == 'build':
            # Use site banner for build pages
            filename = f"social-preview-build-dev-{image_version}.png" if self.is_develop else f"social-preview-build-{image_version}.png"
        else:
            # Use site banner for home page
            filename = f"social-preview-dev-{image_version}.png" if self.is_develop else f"social-preview-{image_version}.png"
        
        return f"{base_url}static/{filename}?v={major_minor}"
    
    def _get_page_title(self, build: CommonBuild) -> str:
        """Generate SEO-optimized page title for a build."""
        display_name = build.get_display_name()
        trial = build.trial_name
        boss = build.boss_name
        role = build.best_player.role.upper() if build.best_player else 'DPS'
        return f"{display_name} {role} Build - {trial} {boss} | ESO Build Guide"
    
    def _get_meta_description(self, build: CommonBuild) -> str:
        """Generate meta description for a build with SEO keywords."""
        display_name = build.get_display_name()
        sets = ' / '.join(build.sets) if build.sets else 'Unknown Sets'
        trial = build.trial_name
        boss = build.boss_name
        role = build.best_player.role.upper() if build.best_player else 'DPS'
        dps = self._format_dps(build.best_player.dps) if build.best_player else 'N/A'
        
        return (
            f"{display_name} {role} build for {trial} {boss} in Elder Scrolls Online. "
            f"{dps} DPS with {sets} gear sets. Complete ESO build guide with abilities, "
            f"gear, and mundus stone. Seen in {build.count} top ESO Logs reports."
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
    def _format_metric(value: float) -> str:
        """
        Format a metric value (DPS/HPS) for display.
        This is an alias for _format_dps to keep template code cleaner.
        """
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
        """Format timestamp for display in local time."""
        if not timestamp_str:
            return "Never"
        
        try:
            from datetime import datetime
            # Parse ISO format timestamp
            dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            # Convert to local time
            local_dt = dt.astimezone()
            return local_dt.strftime('%b %d, %Y at %I:%M %p')
        except (ValueError, TypeError):
            return timestamp_str
    
    @staticmethod
    def _eso_hub_set_url(set_name: str) -> str:
        """
        Generate ESO-Hub URL for a gear set.
        
        Args:
            set_name: Name of the gear set
            
        Returns:
            ESO-Hub URL for the set
            
        Examples:
            "Deadly Strike" -> "https://eso-hub.com/en/sets/deadly-strike"
            "Perfected Slivers of the Null Arca" -> "https://eso-hub.com/en/sets/slivers-of-the-null-arca"
        """
        if not set_name or set_name == 'N/A':
            return '#'
        
        # Remove "Perfected" prefix
        slug = set_name.replace('Perfected ', '')
        
        # Convert to lowercase and slugify
        slug = slug.lower()
        slug = slug.replace("'", '')  # Remove apostrophes
        slug = slug.replace(' ', '-')  # Spaces to dashes
        slug = slug.replace('&', 'and')  # Ampersand to 'and'
        
        return f"https://eso-hub.com/en/sets/{slug}"
    
    @staticmethod
    def _eso_hub_ability_url(ability_name: str) -> str:
        """
        Generate ESO-Hub URL for an ability.
        
        Args:
            ability_name: Name of the ability
            
        Returns:
            ESO-Hub URL for the ability
            
        Examples:
            "Crystal Weapon" -> "https://eso-hub.com/en/skills/crystal-weapon"
        """
        if not ability_name or ability_name == 'Empty':
            return '#'
        
        # Convert to lowercase and slugify
        slug = ability_name.lower()
        slug = slug.replace("'", '')  # Remove apostrophes
        slug = slug.replace(' ', '-')  # Spaces to dashes
        slug = slug.replace('&', 'and')  # Ampersand to 'and'
        
        return f"https://eso-hub.com/en/skills/{slug}"
    
    @staticmethod
    def _eso_hub_mundus_url(mundus_name: str) -> str:
        """
        Generate ESO-Hub URL for a mundus stone.
        
        Args:
            mundus_name: Name of the mundus stone
            
        Returns:
            ESO-Hub URL for the mundus stone
            
        Examples:
            "The Thief" -> "https://eso-hub.com/en/guides/the-thief"
        """
        if not mundus_name or mundus_name == 'Unknown':
            return '#'
        
        # Convert to lowercase and slugify
        slug = mundus_name.lower()
        slug = slug.replace("'", '')  # Remove apostrophes
        slug = slug.replace(' ', '-')  # Spaces to dashes
        
        # Mundus stones are in the guides section
        return f"https://eso-hub.com/en/guides/{slug}"
    
    @staticmethod
    def _trial_background_image(trial_name: str) -> str:
        """
        Get the background image path for a trial.
        
        Args:
            trial_name: Name of the trial (e.g., "Aetherian Archive")
            
        Returns:
            Path to the trial background image
            
        Examples:
            "Aetherian Archive" -> "static/trial-backgrounds/aetherianarchive.png"
            "Dreadsail Reef" -> "static/trial-backgrounds/dreadsail_reef.png"
        """
        # Mapping of trial names to image filenames
        trial_image_map = {
            "Aetherian Archive": "aetherianarchive",
            "Hel Ra Citadel": "helracitadel",
            "Sanctum Ophidia": "sanctum_ophidia",
            "Maw of Lorkhaj": "maw_of_lorkaj",
            "The Halls of Fabrication": "hallsoffabrication",
            "Asylum Sanctorium": "asylumsanctorium",
            "Cloudrest": "cloudrest",
            "Sunspire": "sunspire",
            "Kyne's Aegis": "kynesaegis",
            "Rockgrove": "rockgrove",
            "Dreadsail Reef": "dreadsail_reef",
            "Sanity's Edge": "sanitysedge",
            "Lucent Citadel": "lucentcitadel",
            "Ossein Cage": "ossein_cage",
            "TL;DR: Top Builds": "top-builds"
        }
        
        image_name = trial_image_map.get(trial_name, "")
        if not image_name:
            return ""
        
        return f"static/trial-backgrounds/{image_name}.png"
    
    @staticmethod
    def _trial_social_image(trial_name: str) -> str:
        """
        Get the social card background image path for a trial.
        
        Args:
            trial_name: Name of the trial (e.g., "Aetherian Archive")
            
        Returns:
            Path to the trial social background image
            
        Examples:
            "Aetherian Archive" -> "static/social-backgrounds/aetherianarchive.png"
            "Dreadsail Reef" -> "static/social-backgrounds/dreadsail_reef.png"
        """
        # Mapping of trial names to image filenames
        trial_image_map = {
            "Aetherian Archive": "aetherianarchive",
            "Hel Ra Citadel": "helracitadel",
            "Sanctum Ophidia": "sanctum_ophidia",
            "Maw of Lorkhaj": "maw_of_lorkaj",
            "The Halls of Fabrication": "hallsoffabrication",
            "Asylum Sanctorium": "asylumsanctorium",
            "Cloudrest": "cloudrest",
            "Sunspire": "sunspire",
            "Kyne's Aegis": "kynesaegis",
            "Rockgrove": "rockgrove",
            "Dreadsail Reef": "dreadsail_reef",
            "Sanity's Edge": "sanitysedge",
            "Lucent Citadel": "lucentcitadel",
            "Ossein Cage": "ossein_cage",
            "TL;DR: Top Builds": "top-builds"
        }
        
        image_name = trial_image_map.get(trial_name, "")
        if not image_name:
            return ""
        
        return f"static/social-backgrounds/{image_name}.png"

#!/usr/bin/env python3
"""
Deployment Readiness Check Script

Validates generated HTML pages before deploying to production.
Run this before merging to main to ensure site integrity.

Usage:
    python scripts/deployment_check.py [output_dir]
    
Example:
    python scripts/deployment_check.py output-dev
    python scripts/deployment_check.py output
"""

import sys
import os
from pathlib import Path
from bs4 import BeautifulSoup
from typing import List, Tuple, Optional
import re


class DeploymentChecker:
    """Validates generated site before deployment."""
    
    def __init__(self, output_dir: str = "output"):
        self.output_dir = Path(output_dir)
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.checks_passed = 0
        self.checks_failed = 0
        
    def log_error(self, message: str):
        """Log an error."""
        self.errors.append(f"❌ ERROR: {message}")
        self.checks_failed += 1
        
    def log_warning(self, message: str):
        """Log a warning."""
        self.warnings.append(f"⚠️  WARNING: {message}")
        
    def log_success(self, message: str):
        """Log a success."""
        print(f"✅ {message}")
        self.checks_passed += 1
        
    def read_html(self, file_path: Path) -> Optional[BeautifulSoup]:
        """Read and parse an HTML file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return BeautifulSoup(f.read(), 'html.parser')
        except Exception as e:
            self.log_error(f"Failed to read {file_path}: {e}")
            return None
            
    def check_0_home_page_loads(self) -> bool:
        """Check 0: The home page loads."""
        print("\n" + "="*60)
        print("CHECK 0: Home Page Loads")
        print("="*60)
        
        index_path = self.output_dir / "index.html"
        
        if not index_path.exists():
            self.log_error(f"Home page not found: {index_path}")
            return False
            
        soup = self.read_html(index_path)
        if not soup:
            return False
            
        # Check for essential elements
        title = soup.find('title')
        if not title:
            self.log_error("Home page missing <title> tag")
            return False
            
        # Check for main content (trial names in h3 tags)
        trial_headers = soup.find_all('h3')
        trial_count = len([h for h in trial_headers if any(word in h.text for word in ['Archive', 'Reef', 'Sanctum', 'Spire', 'Grotto', 'Rockgrove', 'Maw', 'Cage'])])
        
        if trial_count == 0:
            self.log_error("Home page has no trials")
            return False
            
        self.log_success(f"Home page loads successfully with {trial_count} trials")
        return True
        
    def check_1_home_page_content(self) -> bool:
        """Check 1: Trials in the home page show boss and build info."""
        print("\n" + "="*60)
        print("CHECK 1: Home Page Trial Content")
        print("="*60)
        
        index_path = self.output_dir / "index.html"
        soup = self.read_html(index_path)
        if not soup:
            return False
            
        # Find all h3 elements (trial names)
        trial_headers = soup.find_all('h3')
        trial_names = [h.text.strip() for h in trial_headers if any(word in h.text for word in ['Archive', 'Reef', 'Sanctum', 'Spire', 'Grotto', 'Rockgrove', 'Maw', 'Cage'])]
        
        for trial_name in trial_names:
            # For each trial, check that it has build information below it
            # Look for div with "Highest DPS Build" text
            has_build_info = False
            for h3 in trial_headers:
                if h3.text.strip() == trial_name:
                    # Find parent and look for build info nearby
                    parent = h3.parent
                    if parent and ("Highest DPS Build" in parent.text or "DPS" in parent.text):
                        has_build_info = True
                        break
                        
            if not has_build_info:
                self.log_warning(f"{trial_name}: Build information might be missing")
            else:
                self.log_success(f"{trial_name}: Has build information")
            
        return self.checks_failed == 0
        
    def check_2_trial_pages(self) -> bool:
        """Check 2: Each trial page shows at least 1 boss and 1 build."""
        print("\n" + "="*60)
        print("CHECK 2: Trial Pages Content")
        print("="*60)
        
        # Find all trial pages (not boss-specific, not build pages)
        trial_pages = []
        for html_file in self.output_dir.glob("*.html"):
            # Skip index, sitemap, and build pages
            if html_file.name == "index.html":
                continue
            if "-" in html_file.stem and not html_file.stem.startswith("dreadsail-reef"):
                # This is likely a build page (has boss-build pattern)
                # But allow trial names with hyphens like "dreadsail-reef"
                continue
                
            # Check if it's a trial page by looking for trial patterns
            trial_name = html_file.stem.replace('-', ' ').title()
            trial_pages.append((html_file, trial_name))
            
        if not trial_pages:
            self.log_error("No trial pages found")
            return False
            
        for trial_file, trial_name in trial_pages:
            soup = self.read_html(trial_file)
            if not soup:
                continue
                
            # Check for boss sections
            boss_sections = soup.find_all('h2', string=re.compile(r'.+'))
            # Filter out non-boss h2s (like "Builds for All Bosses")
            boss_sections = [h2 for h2 in boss_sections if not h2.text.startswith('Builds for')]
            
            # Check for build rows in table
            build_rows = soup.find_all('tr', class_=lambda c: c and 'clickable-row' in c)
            
            if len(boss_sections) < 1:
                self.log_error(f"{trial_name} ({trial_file.name}): No boss sections found")
                continue
                
            if len(build_rows) < 1:
                self.log_error(f"{trial_name} ({trial_file.name}): No builds found")
                continue
                
            self.log_success(f"{trial_name}: Has {len(boss_sections)} boss section(s) and {len(build_rows)} build(s)")
            
        return self.checks_failed == 0
        
    def check_3_build_pages(self) -> bool:
        """Check 3: Build pages have best player, mundus (not unknown), and ability icons."""
        print("\n" + "="*60)
        print("CHECK 3: Build Pages Content")
        print("="*60)
        
        # Find build pages (contain both trial name and build info in filename)
        build_pages = []
        for html_file in self.output_dir.glob("*.html"):
            # Build pages have multiple hyphens and aren't index
            if html_file.name == "index.html":
                continue
            if html_file.stem.count('-') >= 3:  # e.g., aetherian-archive-the-mage-ardent-ass-herald
                build_pages.append(html_file)
                
        if not build_pages:
            self.log_error("No build pages found")
            return False
            
        print(f"Found {len(build_pages)} build pages to check")
        
        # Check a sample of build pages (first 10, or all if less)
        sample_size = min(10, len(build_pages))
        for build_file in build_pages[:sample_size]:
            soup = self.read_html(build_file)
            if not soup:
                continue
                
            build_name = build_file.stem[:50] + "..." if len(build_file.stem) > 50 else build_file.stem
            
            # Check for best player (character name in h1 subtitle)
            player_elem = soup.find('p', class_='subtitle')
            if not player_elem:
                self.log_error(f"{build_name}: No best player found")
                continue
                
            player_name = player_elem.text.strip()
            if not player_name or player_name == "Unknown":
                self.log_error(f"{build_name}: Best player is Unknown")
                continue
                
            # Check for mundus stone
            mundus_found = False
            mundus_value = "Unknown"
            info_boxes = soup.find_all('div', class_='info-box')
            for box in info_boxes:
                label = box.find('div', class_='label')
                if label and 'Mundus' in label.text:
                    value = box.find('div', class_='value')
                    if value:
                        mundus_value = value.text.strip()
                        mundus_found = True
                        break
                        
            if not mundus_found:
                self.log_error(f"{build_name}: Mundus field not found")
                continue
                
            if mundus_value == "Unknown" or not mundus_value:
                self.log_error(f"{build_name}: Mundus is Unknown or empty")
                continue
                
            # Check for ability icons
            ability_slots = soup.find_all('div', class_='ability-slot')
            if not ability_slots:
                self.log_warning(f"{build_name}: No ability slots found")
            else:
                missing_icons = []
                for slot in ability_slots:
                    img = slot.find('img')
                    if img and img.get('src'):
                        # Check if it's the default "Empty" icon
                        if 'Empty' in img['src']:
                            # This is expected for empty slots
                            continue
                        # Check if src is a valid path (not broken)
                        if img['src'].startswith('http') or img['src'].startswith('/'):
                            # External or absolute path
                            continue
                        # Relative path - check if file exists
                        icon_path = self.output_dir / img['src']
                        if not icon_path.exists():
                            missing_icons.append(img['src'])
                    elif not img:
                        missing_icons.append("(no img tag)")
                        
                if missing_icons:
                    self.log_warning(f"{build_name}: Missing {len(missing_icons)} ability icon(s)")
                    
            self.log_success(f"{build_name[:40]}...: Player={player_name[:20]}, Mundus={mundus_value}")
            
        print(f"\n✓ Checked {sample_size} of {len(build_pages)} build pages")
        
        return self.checks_failed == 0
        
    def run_all_checks(self) -> bool:
        """Run all deployment checks."""
        print("\n" + "="*70)
        print("ESO BUILD-O-RAMA DEPLOYMENT READINESS CHECK")
        print("="*70)
        print(f"Output Directory: {self.output_dir.absolute()}")
        
        # Run checks in order
        check_0 = self.check_0_home_page_loads()
        check_1 = self.check_1_home_page_content()
        check_2 = self.check_2_trial_pages()
        check_3 = self.check_3_build_pages()
        
        # Print summary
        print("\n" + "="*70)
        print("SUMMARY")
        print("="*70)
        print(f"✅ Checks Passed: {self.checks_passed}")
        print(f"❌ Checks Failed: {self.checks_failed}")
        
        if self.warnings:
            print(f"\n⚠️  Warnings ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"  {warning}")
                
        if self.errors:
            print(f"\n❌ Errors ({len(self.errors)}):")
            for error in self.errors:
                print(f"  {error}")
        else:
            print("\n🎉 All checks passed! Ready to deploy.")
            
        print("="*70)
        
        return len(self.errors) == 0


def main():
    """Main entry point."""
    # Get output directory from command line or use default
    output_dir = sys.argv[1] if len(sys.argv) > 1 else "output"
    
    # Check if output directory exists
    if not Path(output_dir).exists():
        print(f"❌ Error: Output directory '{output_dir}' does not exist")
        print(f"\nUsage: python {sys.argv[0]} [output_dir]")
        print(f"Example: python {sys.argv[0]} output-dev")
        sys.exit(1)
        
    # Run checks
    checker = DeploymentChecker(output_dir)
    success = checker.run_all_checks()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

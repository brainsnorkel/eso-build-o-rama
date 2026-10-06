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
import json
from pathlib import Path
from bs4 import BeautifulSoup
from typing import List, Tuple, Optional
import re

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.eso_build_o_rama.models import CLASS_SKILL_LINES  # noqa: E402

NON_BUILD_PAGES = {"index.html", "about.html", "tldr-top-builds.html", "build-finder.html"}
CANONICAL_CLASS_SLUGS = {name.lower() for name in CLASS_SKILL_LINES}
VALID_ROLES = {"dps", "healer", "tank"}


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
            
    def _trial_page_stems(self) -> set:
        """Return trial page filename stems as written by generate_trial_page (apostrophes kept)."""
        trials_path = PROJECT_ROOT / "data" / "trials.json"
        try:
            with open(trials_path, "r", encoding="utf-8") as f:
                trials = json.load(f)["trials"]
        except FileNotFoundError:
            self.log_error(f"Trials config not found: {trials_path}")
            return set()
        return {t["name"].lower().replace(" ", "-") for t in trials}

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
        
        trial_names = self._trial_page_stems()
        
        # Find trial pages by matching against known trial names
        trial_pages = []
        for html_file in self.output_dir.glob("*.html"):
            # Skip index
            if html_file.name == "index.html":
                continue
                
            # Check if this filename matches a known trial name
            file_stem = html_file.stem
            if file_stem in trial_names:
                trial_name = file_stem.replace('-', ' ').title()
                trial_pages.append((html_file, trial_name))
            
        if not trial_pages:
            self.log_error("No trial pages found")
            return False
            
        for trial_file, trial_name in trial_pages:
            soup = self.read_html(trial_file)
            if not soup:
                continue
                
            # Check for boss sections (h2 tags)
            boss_sections = soup.find_all('h2')
            # Filter out non-boss h2s (like "Builds for All Bosses")
            boss_sections = [h2 for h2 in boss_sections if h2.text.strip() and not h2.text.startswith('Builds for')]
            
            # Check for build rows in table (trial pages have plain <tr> tags in tbody)
            tables = soup.find_all('table')
            build_rows = []
            for table in tables:
                tbody = table.find('tbody')
                if tbody:
                    build_rows.extend(tbody.find_all('tr'))
            
            if len(boss_sections) < 1:
                self.log_warning(f"{trial_name} ({trial_file.name}): No boss sections found (may not have been generated yet)")
                continue
                
            if len(build_rows) < 1:
                self.log_warning(f"{trial_name} ({trial_file.name}): No builds found (may not have been generated yet)")
                continue
                
            self.log_success(f"{trial_name}: Has {len(boss_sections)} boss section(s) and {len(build_rows)} build(s)")
            
        return self.checks_failed == 0
        
    def check_3_build_pages(self) -> bool:
        """Check 3: Build pages have best player, mundus (not unknown), and ability icons."""
        print("\n" + "="*60)
        print("CHECK 3: Build Pages Content")
        print("="*60)
        
        # Trial pages are excluded from build page detection
        trial_names = self._trial_page_stems()
        
        # Find build pages (not index, not trial pages)
        build_pages = []
        for html_file in self.output_dir.glob("*.html"):
            # Skip index, other non-build pages, and trial pages
            if html_file.name in NON_BUILD_PAGES:
                continue
            if html_file.stem in trial_names:
                continue
            # Remaining pages are build pages
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
                
            # Check for ability icons (build_page.html: div.abilities-bar > div.ability > img.ability-icon)
            ability_slots = soup.select('div.abilities-bar > div.ability')
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
                        # Relative path - resolve against the page, as a browser would
                        icon_path = build_file.parent / img['src']
                        if not icon_path.exists():
                            missing_icons.append(img['src'])
                    elif not img:
                        missing_icons.append("(no img tag)")
                        
                if missing_icons:
                    self.log_warning(f"{build_name}: Missing {len(missing_icons)} ability icon(s)")
                    
            self.log_success(f"{build_name[:40]}...: Player={player_name[:20]}, Mundus={mundus_value}")
            
        print(f"\n✓ Checked {sample_size} of {len(build_pages)} build pages")
        
        return self.checks_failed == 0
        
    def check_4_build_finder(self) -> bool:
        """Check 4: Build Finder page has valid filters and rows."""
        print("\n" + "="*60)
        print("CHECK 4: Build Finder Page")
        print("="*60)

        finder_path = self.output_dir / "build-finder.html"
        if not finder_path.exists():
            self.log_error(f"Build finder page not found: {finder_path}")
            return False

        soup = self.read_html(finder_path)
        if not soup:
            return False

        class_select = soup.find('select', id='finder-class')
        role_select = soup.find('select', id='finder-role')
        if not class_select or not role_select:
            self.log_error("Build finder missing #finder-class and/or #finder-role select")
            return False

        class_values = [o.get('value', '') for o in class_select.find_all('option')]
        role_values = [o.get('value', '') for o in role_select.find_all('option')]
        bad_classes = [v for v in class_values if v != "" and v not in CANONICAL_CLASS_SLUGS]
        bad_roles = [v for v in role_values if v != "" and v not in VALID_ROLES]
        if bad_classes:
            self.log_error(f"Build finder class select has non-canonical values: {bad_classes}")
        if bad_roles:
            self.log_error(f"Build finder role select has invalid values: {bad_roles}")
        if len(class_values) < 2:
            self.log_error("Build finder class select has fewer than 2 options")

        table = soup.find('table', id='finder-table')
        if not table:
            self.log_error("Build finder missing #finder-table")
            return False
        tbody = table.find('tbody')
        rows = [tr for tr in (tbody.find_all('tr') if tbody else []) if tr.get('id') != 'finder-empty']
        if len(rows) < 1:
            self.log_error("Build finder table has no data rows")
            return False

        # Compare finder build links with build pages on disk
        trial_names = self._trial_page_stems()
        build_pages = {
            f.name for f in self.output_dir.glob("*.html")
            if f.name not in NON_BUILD_PAGES
            and f.stem not in trial_names
            and not f.name.startswith("tldr-")
        }
        finder_targets = {
            (a.get('href') or '').split('#')[0].split('?')[0]
            for row in rows for a in row.find_all('a', class_='finder-build-link')
        }
        if finder_targets != build_pages:
            not_on_disk = sorted(finder_targets - build_pages)
            not_in_finder = sorted(build_pages - finder_targets)
            self.log_warning(
                f"Build finder links and build pages differ: "
                f"{len(not_on_disk)} linked but not a build page {not_on_disk[:10]}; "
                f"{len(not_in_finder)} build pages not in finder {not_in_finder[:10]}"
            )

        problems: List[str] = []
        problem_count = 0

        def problem(msg: str):
            nonlocal problem_count
            problem_count += 1
            if len(problems) < 10:
                problems.append(msg)

        classes_seen = set()
        roles_seen = set()
        for i, row in enumerate(rows, 1):
            data_class = row.get('data-class')
            data_role = row.get('data-role')
            if data_class not in CANONICAL_CLASS_SLUGS:
                problem(f"row {i}: invalid data-class {data_class!r}")
            else:
                classes_seen.add(data_class)
            if data_role not in VALID_ROLES:
                problem(f"row {i}: invalid data-role {data_role!r}")
            else:
                roles_seen.add(data_role)
            if not row.has_attr('data-trash'):
                problem(f"row {i}: missing data-trash")

            build_links = row.find_all('a', class_='finder-build-link')
            if len(build_links) != 1:
                problem(f"row {i}: expected 1 .finder-build-link, found {len(build_links)}")
            else:
                href = (build_links[0].get('href') or '').split('#')[0].split('?')[0]
                if not href or not (self.output_dir / href).is_file():
                    problem(f"row {i}: build link target missing: {href!r}")

            esologs_links = row.find_all('a', class_='finder-esologs-link')
            if len(esologs_links) > 1:
                problem(f"row {i}: expected at most 1 .finder-esologs-link, found {len(esologs_links)}")
            elif esologs_links and not (esologs_links[0].get('href') or '').startswith("https://www.esologs.com/"):
                problem(f"row {i}: esologs link href invalid: {esologs_links[0].get('href')!r}")

            if any(not td.has_attr('data-label') for td in row.find_all('td')):
                problem(f"row {i}: td missing data-label")

        if problem_count:
            self.log_error(f"Build finder: {problem_count} problem(s); examples: " + "; ".join(problems))
            return False

        self.log_success(f"Build finder: {len(rows)} rows, {len(classes_seen)} classes, {len(roles_seen)} roles")
        return self.checks_failed == 0

    def check_5_builds_json_icons(self) -> bool:
        """Check 5: Every ability_icon referenced in builds.json has a PNG in <output_dir>/static/icons."""
        print("\n" + "="*60)
        print("CHECK 5: builds.json Ability Icons")
        print("="*60)

        builds_path = self.output_dir / "builds.json"
        if not builds_path.exists():
            self.log_error(f"builds.json not found: {builds_path}")
            return False
        try:
            with open(builds_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            self.log_error(f"Failed to read {builds_path}: {e}")
            return False

        referenced = {}  # stem -> ability name

        def walk(obj):
            if isinstance(obj, dict):
                if "best_player" in obj and "build_slug" in obj:
                    for player in (obj.get("all_players") or []) + [obj.get("best_player")]:
                        for bar in ("abilities_bar1", "abilities_bar2"):
                            for ab in (player or {}).get(bar) or []:
                                stem = ab.get("ability_icon")
                                if stem:
                                    referenced.setdefault(stem, ab.get("ability_name") or "?")
                    return
                for v in obj.values():
                    walk(v)
            elif isinstance(obj, list):
                for v in obj:
                    walk(v)

        walk(data)
        icons_dir = self.output_dir / "static" / "icons"
        missing = sorted((s, n) for s, n in referenced.items() if not (icons_dir / f"{s}.png").is_file())
        if missing:
            listing = ", ".join(f"{s} ({n})" for s, n in missing[:20])
            self.log_error(f"{len(missing)} of {len(referenced)} ability icons referenced in builds.json "
                           f"missing from {icons_dir}: {listing}")
            return False
        self.log_success(f"All {len(referenced)} ability icons referenced in builds.json exist in {icons_dir}")
        return True

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
        check_4 = self.check_4_build_finder()
        check_5 = self.check_5_builds_json_icons()
        
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

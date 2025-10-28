#!/usr/bin/env python3
"""
Regenerate all pages from existing builds.json data.
This is useful when template changes need to be applied to all pages.
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.eso_build_o_rama.page_generator import PageGenerator
from src.eso_build_o_rama.data_store import DataStore
from src.eso_build_o_rama.build_analyzer import BuildAnalyzer

def main():
    """Regenerate all pages from existing builds.json."""

    # Determine which output directory to use
    output_dir = "output"  # Default to production
    if len(sys.argv) > 1:
        output_dir = sys.argv[1]

    print(f"Regenerating pages in: {output_dir}/")

    # Initialize components
    data_store = DataStore(builds_file=f"{output_dir}/builds.json")
    page_generator = PageGenerator(template_dir="templates", output_dir=output_dir)

    # Get all saved builds
    all_saved_builds = data_store.get_all_builds()
    trials_metadata = data_store.get_trials_metadata()

    print(f"Found {len(all_saved_builds)} saved builds")
    print(f"Trials with data: {list(trials_metadata.get('trials', {}).keys())}")

    # Get version
    version_file = Path(__file__).parent / 'VERSION'
    try:
        app_version = version_file.read_text().strip()
    except FileNotFoundError:
        app_version = "1.0.0"

    # Determine update version
    update_version = trials_metadata.get('update_version', 'unknown')

    # Generate TL;DR aggregated builds
    print("\nGenerating TL;DR aggregated builds...")
    build_analyzer = BuildAnalyzer()
    aggregated_builds = build_analyzer.aggregate_builds_across_trials(all_saved_builds)

    # Generate TL;DR summary page
    tldr_path = page_generator.generate_tldr_summary_page(aggregated_builds, app_version)
    print(f"Generated TL;DR summary: {tldr_path}")

    # Generate aggregated build pages
    for role, builds in aggregated_builds.items():
        for build in builds:
            agg_path = page_generator.generate_aggregated_build_page(build, update_version, app_version)
            print(f"Generated aggregated build: {agg_path}")

    # Generate all pages
    print("\nGenerating all trial and build pages...")
    generated_files = page_generator.generate_all_pages(
        all_builds=all_saved_builds,
        update_version=update_version,
        trials_metadata=trials_metadata,
        app_version=app_version,
        aggregated_builds=aggregated_builds
    )

    print(f"\n✅ Regenerated {len(generated_files)} HTML files:")
    for key, path in sorted(generated_files.items())[:10]:
        print(f"  - {path}")
    if len(generated_files) > 10:
        print(f"  ... and {len(generated_files) - 10} more")


if __name__ == "__main__":
    main()

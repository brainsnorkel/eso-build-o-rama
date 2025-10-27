#!/usr/bin/env python3
"""
Generate empty pages showing "No data yet" for all trials.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.eso_build_o_rama.page_generator import PageGenerator
from src.eso_build_o_rama.data_store import DataStore


def main():
    """Generate pages with empty data."""
    # Initialize components
    data_store = DataStore(builds_file="output-dev/builds.json")
    page_generator = PageGenerator(template_dir="templates", output_dir="output-dev")

    # Get all saved builds (should be empty)
    all_saved_builds = data_store.get_all_builds()
    trials_metadata = data_store.get_trials_metadata()

    print(f"Found {len(all_saved_builds)} saved builds")
    print(f"Trials metadata: {trials_metadata}")

    # Generate pages
    generated_files = page_generator.generate_all_pages(
        all_builds=all_saved_builds,
        update_version="unknown",
        trials_metadata=trials_metadata,
        app_version="1.0.0",
        aggregated_builds={}
    )

    print(f"\nGenerated {len(generated_files)} HTML files:")
    for key, path in generated_files.items():
        print(f"  - {key}: {path}")


if __name__ == "__main__":
    main()

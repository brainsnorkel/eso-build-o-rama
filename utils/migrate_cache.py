#!/usr/bin/env python3
"""
Migrate existing cache files to the new subdirectory structure.

This script moves cache files from the root cache directory to their appropriate subdirectories:
- buffs_* files -> cache/buffs/
- table_* files -> cache/tables/
- fight_rankings_* files -> cache/rankings/ (and renames to rankings_*)
- Other files remain in root (zones.json, etc.)
"""

import os
import shutil
from pathlib import Path
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def migrate_cache_files(cache_dir: str = "cache", dry_run: bool = False) -> dict:
    """
    Migrate cache files to new subdirectory structure.
    
    Args:
        cache_dir: Path to cache directory (default: "cache")
        dry_run: If True, only show what would be done without actually moving files
        
    Returns:
        Dictionary with migration statistics
    """
    cache_path = Path(cache_dir)
    
    if not cache_path.exists():
        logger.error(f"Cache directory not found: {cache_dir}")
        return {}
    
    stats = {
        "buffs_moved": 0,
        "tables_moved": 0,
        "rankings_moved": 0,
        "rankings_renamed": 0,
        "skipped": 0,
        "errors": 0
    }
    
    # Ensure subdirectories exist
    subdirs = ["buffs", "tables", "rankings"]
    if not dry_run:
        for subdir in subdirs:
            (cache_path / subdir).mkdir(exist_ok=True)
    
    # Iterate through all files in cache root
    for file_path in cache_path.glob("*.json"):
        if file_path.is_file():
            filename = file_path.name
            
            try:
                # Determine destination based on filename prefix
                if filename.startswith("buffs_"):
                    # Move to buffs subdirectory
                    dest_path = cache_path / "buffs" / filename
                    if not dry_run:
                        shutil.move(str(file_path), str(dest_path))
                    logger.info(f"{'[DRY RUN] Would move' if dry_run else 'Moved'} {filename} -> buffs/")
                    stats["buffs_moved"] += 1
                    
                elif filename.startswith("table_"):
                    # Move to tables subdirectory
                    dest_path = cache_path / "tables" / filename
                    if not dry_run:
                        shutil.move(str(file_path), str(dest_path))
                    logger.info(f"{'[DRY RUN] Would move' if dry_run else 'Moved'} {filename} -> tables/")
                    stats["tables_moved"] += 1
                    
                elif filename.startswith("fight_rankings_"):
                    # Rename to rankings_ and move to rankings subdirectory
                    new_filename = filename.replace("fight_rankings_", "rankings_")
                    dest_path = cache_path / "rankings" / new_filename
                    if not dry_run:
                        shutil.move(str(file_path), str(dest_path))
                    logger.info(f"{'[DRY RUN] Would move' if dry_run else 'Moved'} {filename} -> rankings/{new_filename}")
                    stats["rankings_moved"] += 1
                    stats["rankings_renamed"] += 1
                    
                else:
                    # Skip files that should stay in root (zones.json, etc.)
                    logger.debug(f"Skipping {filename} (should remain in root)")
                    stats["skipped"] += 1
                    
            except Exception as e:
                logger.error(f"Error processing {filename}: {e}")
                stats["errors"] += 1
    
    return stats


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Migrate cache files to new subdirectory structure')
    parser.add_argument('--cache-dir', type=str, default='cache', help='Cache directory path (default: cache)')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done without actually moving files')
    
    args = parser.parse_args()
    
    logger.info("="*60)
    logger.info("Cache Migration Utility")
    logger.info("="*60)
    
    if args.dry_run:
        logger.info("DRY RUN MODE - No files will be moved")
    
    stats = migrate_cache_files(cache_dir=args.cache_dir, dry_run=args.dry_run)
    
    logger.info("\n" + "="*60)
    logger.info("Migration Summary")
    logger.info("="*60)
    logger.info(f"Buffs files moved: {stats.get('buffs_moved', 0)}")
    logger.info(f"Table files moved: {stats.get('tables_moved', 0)}")
    logger.info(f"Rankings files moved: {stats.get('rankings_moved', 0)}")
    logger.info(f"Rankings files renamed: {stats.get('rankings_renamed', 0)}")
    logger.info(f"Files skipped (remain in root): {stats.get('skipped', 0)}")
    logger.info(f"Errors: {stats.get('errors', 0)}")
    logger.info("="*60)
    
    if args.dry_run:
        logger.info("\nRun without --dry-run to perform the migration")
    else:
        logger.info("\nMigration complete!")


if __name__ == "__main__":
    main()


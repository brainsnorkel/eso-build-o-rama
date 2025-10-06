"""
Cache manager for ESO Logs API responses.

This module handles caching of immutable API responses to improve performance
and reduce API rate limiting. Since ESO Logs reports are immutable once created,
we can cache them indefinitely.
"""

import json
import hashlib
from pathlib import Path
from typing import Any, Dict, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class CacheManager:
    """
    Manages caching of API responses to disk.
    
    Cache structure:
    cache/
      reports/
        {report_code}.json          # Full report data
      rankings/
        zone_{zone_id}_enc_{encounter_id}_top_{limit}.json  # Rankings data
      zones.json                    # Zone/encounter list
    """
    
    def __init__(self, cache_dir: str = "cache"):
        """
        Initialize cache manager.
        
        Args:
            cache_dir: Directory to store cache files
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        
        # Create subdirectories
        (self.cache_dir / "reports").mkdir(exist_ok=True)
        (self.cache_dir / "rankings").mkdir(exist_ok=True)
        
        # Cache hit/miss counters
        self.cache_hits = 0
        self.cache_misses = 0
    
    def _get_cache_path(self, cache_key: str) -> Path:
        """
        Get the file path for a cache key.
        
        Args:
            cache_key: The cache key (e.g., "report_abc123", "rankings_1_2_10")
            
        Returns:
            Path to the cache file
        """
        # Determine subdirectory based on key prefix
        if cache_key.startswith("report_"):
            subdir = "reports"
            filename = f"{cache_key[7:]}.json"  # Remove "report_" prefix
        elif cache_key.startswith("rankings_"):
            subdir = "rankings"
            filename = f"{cache_key[9:]}.json"  # Remove "rankings_" prefix
        elif cache_key == "zones":
            subdir = ""
            filename = "zones.json"
        else:
            # Generic cache file
            subdir = ""
            filename = f"{cache_key}.json"
        
        if subdir:
            return self.cache_dir / subdir / filename
        else:
            return self.cache_dir / filename
    
    def cache_exists(self, cache_key: str) -> bool:
        """
        Check if a cached response exists.
        
        Args:
            cache_key: The cache key
            
        Returns:
            True if cached response exists
        """
        cache_path = self._get_cache_path(cache_key)
        return cache_path.exists()
    
    def get_cached_response(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """
        Get a cached API response.
        
        Args:
            cache_key: The cache key
            
        Returns:
            Cached response data, or None if not found
        """
        cache_path = self._get_cache_path(cache_key)
        
        if not cache_path.exists():
            self.cache_misses += 1
            return None
        
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                logger.debug(f"Loaded cached response: {cache_key}")
                self.cache_hits += 1
                return data
        except (IOError, json.JSONDecodeError) as e:
            logger.warning(f"Failed to load cached response {cache_key}: {e}")
            self.cache_misses += 1
            return None
    
    def save_cached_response(self, cache_key: str, data: Any) -> None:
        """
        Save an API response to cache.
        
        Args:
            cache_key: The cache key
            data: Response data to cache (can be any type)
        """
        cache_path = self._get_cache_path(cache_key)
        
        try:
            # Ensure parent directory exists
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Convert data to JSON-serializable format
            serializable_data = self._make_serializable(data)
            
            # Add metadata
            cached_data = {
                "cached_at": datetime.utcnow().isoformat(),
                "cache_key": cache_key,
                "data": serializable_data
            }
            
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(cached_data, f, indent=2, ensure_ascii=False)
                logger.debug(f"Saved cached response: {cache_key}")
        except (IOError, TypeError) as e:
            logger.error(f"Failed to save cached response {cache_key}: {e}")
    
    def _make_serializable(self, obj: Any) -> Any:
        """
        Convert an object to JSON-serializable format.
        
        Args:
            obj: Object to convert
            
        Returns:
            JSON-serializable version of the object
        """
        if obj is None:
            return None
        elif isinstance(obj, (str, int, float, bool)):
            return obj
        elif isinstance(obj, (list, tuple)):
            return [self._make_serializable(item) for item in obj]
        elif isinstance(obj, dict):
            return {key: self._make_serializable(value) for key, value in obj.items()}
        elif hasattr(obj, '__dict__'):
            # Convert custom objects to dictionaries
            try:
                return self._make_serializable(obj.__dict__)
            except Exception:
                # If __dict__ fails, try to convert to string
                return str(obj)
        else:
            # For any other type, convert to string
            return str(obj)
    
    def clear_cache(self) -> None:
        """
        Clear all cached responses.
        """
        import shutil
        try:
            if self.cache_dir.exists():
                shutil.rmtree(self.cache_dir)
                self.cache_dir.mkdir(exist_ok=True)
                (self.cache_dir / "reports").mkdir(exist_ok=True)
                (self.cache_dir / "rankings").mkdir(exist_ok=True)
                logger.info("Cleared all cached responses")
        except OSError as e:
            logger.error(f"Failed to clear cache: {e}")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the cache.
        
        Returns:
            Dictionary with cache statistics
        """
        stats = {
            "cache_dir": str(self.cache_dir),
            "total_files": 0,
            "total_size_bytes": 0,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "by_type": {
                "reports": {"count": 0, "size_bytes": 0},
                "rankings": {"count": 0, "size_bytes": 0},
                "other": {"count": 0, "size_bytes": 0}
            }
        }
        
        try:
            for cache_file in self.cache_dir.rglob("*.json"):
                if cache_file.is_file():
                    stats["total_files"] += 1
                    file_size = cache_file.stat().st_size
                    stats["total_size_bytes"] += file_size
                    
                    # Categorize by subdirectory
                    if "reports" in str(cache_file):
                        stats["by_type"]["reports"]["count"] += 1
                        stats["by_type"]["reports"]["size_bytes"] += file_size
                    elif "rankings" in str(cache_file):
                        stats["by_type"]["rankings"]["count"] += 1
                        stats["by_type"]["rankings"]["size_bytes"] += file_size
                    else:
                        stats["by_type"]["other"]["count"] += 1
                        stats["by_type"]["other"]["size_bytes"] += file_size
        except OSError as e:
            logger.error(f"Failed to get cache stats: {e}")
        
        return stats

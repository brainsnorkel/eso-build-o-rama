#!/usr/bin/env python3
"""
Verify Social Card Deployment
Compares social preview images between GitHub source and live esobuild.com site.
"""

import requests
import hashlib
from pathlib import Path
from typing import Dict, Tuple
import sys


class SocialCardVerifier:
    """Verify that social preview images are correctly deployed."""
    
    def __init__(self):
        # GitHub raw content URL (what should be deployed)
        self.github_base = "https://raw.githubusercontent.com/brainsnorkel/eso-build-o-rama/main/output/static/"
        
        # Live site URL (what's actually being served)
        self.live_base = "https://esobuild.com/static/"
        
        # Social preview files to check
        self.files_to_check = [
            "social-preview.png",  # Home page
            "social-preview-dev.png",  # Home page (dev)
            "social-preview-build.png",  # Build pages
            "social-preview-build-dev.png",  # Build pages (dev)
        ]
        
        # Add trial-specific previews
        trials = [
            'aetherianarchive', 'helracitadel', 'sanctumophidia',
            'mawoflorkhaj', 'thehallsoffabrication', 'asylumsanctorium',
            'cloudrest', 'sunspire', "kyne'saegis", 'rockgrove',
            'dreadsailreef', "sanity'sedge", 'lucentcitadel', 'osseincage'
        ]
        
        for trial in trials:
            self.files_to_check.append(f"social-preview-{trial}.png")
            self.files_to_check.append(f"social-preview-{trial}-dev.png")
    
    def get_file_info(self, url: str) -> Tuple[int, str, dict]:
        """
        Get file size, hash, and headers from URL.
        
        Returns:
            Tuple of (size_bytes, md5_hash, headers_dict)
        """
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                content = response.content
                size = len(content)
                md5 = hashlib.md5(content).hexdigest()
                headers = dict(response.headers)
                return size, md5, headers
            else:
                return 0, "", {"error": f"HTTP {response.status_code}"}
        except Exception as e:
            return 0, "", {"error": str(e)}
    
    def verify_all(self) -> Dict[str, dict]:
        """
        Verify all social preview images.
        
        Returns:
            Dictionary of results for each file
        """
        results = {}
        
        print("🔍 Verifying Social Preview Images")
        print("=" * 80)
        print()
        
        matched = 0
        mismatched = 0
        errors = 0
        
        for filename in self.files_to_check:
            github_url = self.github_base + filename
            live_url = self.live_base + filename
            
            # Get GitHub version (source of truth)
            github_size, github_hash, github_headers = self.get_file_info(github_url)
            
            # Get live version (what's being served)
            live_size, live_hash, live_headers = self.get_file_info(live_url)
            
            # Compare
            if github_hash and live_hash:
                match = (github_hash == live_hash)
                
                if match:
                    status = "✅ MATCH"
                    matched += 1
                else:
                    status = "❌ MISMATCH"
                    mismatched += 1
                
                results[filename] = {
                    "status": status,
                    "github_size": github_size,
                    "live_size": live_size,
                    "size_diff": abs(github_size - live_size),
                    "github_hash": github_hash[:8],
                    "live_hash": live_hash[:8],
                    "cache_status": live_headers.get('cf-cache-status', 'N/A'),
                    "age": live_headers.get('age', 'N/A'),
                    "last_modified": live_headers.get('last-modified', 'N/A')
                }
                
                # Print summary for important files
                if filename in ['social-preview.png', 'social-preview-build.png']:
                    print(f"📄 {filename}")
                    print(f"   Status: {status}")
                    print(f"   GitHub: {github_size:,} bytes | Hash: {github_hash[:8]}")
                    print(f"   Live:   {live_size:,} bytes | Hash: {live_hash[:8]}")
                    if not match:
                        print(f"   ⚠️  Difference: {abs(github_size - live_size):,} bytes")
                    print(f"   Cache: {live_headers.get('cf-cache-status', 'N/A')} | Age: {live_headers.get('age', 'N/A')}s")
                    print(f"   Modified: {live_headers.get('last-modified', 'N/A')}")
                    print()
            else:
                status = "⚠️  ERROR"
                errors += 1
                error_msg = github_headers.get('error', '') or live_headers.get('error', '')
                results[filename] = {
                    "status": status,
                    "error": error_msg
                }
        
        # Print summary
        print()
        print("=" * 80)
        print("📊 SUMMARY")
        print("=" * 80)
        print(f"  Total files checked: {len(self.files_to_check)}")
        print(f"  ✅ Matched: {matched}")
        print(f"  ❌ Mismatched: {mismatched}")
        print(f"  ⚠️  Errors: {errors}")
        print()
        
        if mismatched > 0:
            print("❌ DEPLOYMENT MISMATCH DETECTED!")
            print("   Some files on esobuild.com differ from GitHub source.")
            print("   Possible causes:")
            print("   • Cloudflare cache not fully purged")
            print("   • GitHub Pages hasn't deployed yet")
            print("   • Propagation delay in CDN")
        elif errors > 0:
            print("⚠️  Some files could not be verified (may not exist yet)")
        else:
            print("✅ ALL FILES MATCH!")
            print("   GitHub source and live site are in sync.")
        
        return results


def main():
    """Run the verification."""
    verifier = SocialCardVerifier()
    results = verifier.verify_all()
    
    # Exit with error code if there are mismatches
    mismatches = sum(1 for r in results.values() if r.get('status') == '❌ MISMATCH')
    sys.exit(1 if mismatches > 0 else 0)


if __name__ == "__main__":
    main()


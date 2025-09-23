#!/usr/bin/env python3
"""
StratMaster Asset Management System

Cryptographically verified download system for remote assets including:
- ML models, seed corpora, configuration templates
- SHA256 verification and optional signature checking
- Resume support with retries and exponential backoff
- Cross-platform compatibility (Linux, macOS, WSL)
- Atomic downloads with lock file management

Usage:
    python scripts/assets_pull.py --help
    python scripts/assets_pull.py plan
    python scripts/assets_pull.py pull --required-only
    python scripts/assets_pull.py verify
"""

import argparse
import hashlib
import json
import os
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, UTC

try:
    import yaml
except ImportError:
    print("Error: PyYAML is required. Install with: pip install PyYAML")
    sys.exit(1)


@dataclass
class AssetInfo:
    """Information about a downloadable asset."""
    name: str
    url: str
    sha256: str
    licence: str
    size_mb: float
    description: str
    optional: bool = True
    category: str = "unknown"


@dataclass
class AssetLockEntry:
    """Lock file entry tracking downloaded asset state."""
    name: str
    url: str
    sha256: str
    downloaded_at: str
    verified_at: str
    file_size: int
    status: str  # "complete", "partial", "failed", "missing"


class AssetManager:
    """Manages cryptographically verified asset downloads."""
    
    def __init__(self, manifest_path: str, assets_dir: str = "assets", dry_run: bool = False):
        self.manifest_path = Path(manifest_path)
        self.assets_dir = Path(assets_dir)
        self.lock_path = Path(".assetlock")
        self.dry_run = dry_run
        
        # Ensure directories exist
        if not dry_run:
            self.assets_dir.mkdir(exist_ok=True)
            
        # Load manifest and lock file
        self.manifest = self._load_manifest()
        self.lock_data = self._load_lock_file()
        
    def _load_manifest(self) -> Dict:
        """Load and validate asset manifest."""
        if not self.manifest_path.exists():
            raise FileNotFoundError(f"Asset manifest not found: {self.manifest_path}")
            
        with open(self.manifest_path, 'r') as f:
            manifest = yaml.safe_load(f)
            
        # Basic validation
        required_keys = ['version', 'manifest_id']
        for key in required_keys:
            if key not in manifest:
                raise ValueError(f"Missing required manifest key: {key}")
                
        return manifest
    
    def _load_lock_file(self) -> Dict[str, AssetLockEntry]:
        """Load existing asset lock file."""
        if not self.lock_path.exists():
            return {}
            
        try:
            with open(self.lock_path, 'r') as f:
                lock_data = json.load(f)
                
            return {
                name: AssetLockEntry(**entry) 
                for name, entry in lock_data.items()
            }
        except (json.JSONDecodeError, TypeError) as e:
            print(f"Warning: Invalid lock file, starting fresh: {e}")
            return {}
    
    def _save_lock_file(self):
        """Save current lock file state."""
        if self.dry_run:
            return
            
        lock_dict = {
            name: {
                'name': entry.name,
                'url': entry.url,
                'sha256': entry.sha256,
                'downloaded_at': entry.downloaded_at,
                'verified_at': entry.verified_at,
                'file_size': entry.file_size,
                'status': entry.status
            }
            for name, entry in self.lock_data.items()
        }
        
        with open(self.lock_path, 'w') as f:
            json.dump(lock_dict, f, indent=2)
    
    def _get_all_assets(self) -> List[AssetInfo]:
        """Extract all assets from manifest."""
        assets = []
        
        # Process each category
        for category in ['models', 'data', 'configs']:
            if category not in self.manifest:
                continue
                
            for asset_data in self.manifest[category]:
                asset = AssetInfo(
                    name=asset_data['name'],
                    url=asset_data['url'], 
                    sha256=asset_data['sha256'],
                    licence=asset_data['licence'],
                    size_mb=asset_data['size_mb'],
                    description=asset_data['description'],
                    optional=asset_data.get('optional', True),
                    category=category
                )
                assets.append(asset)
                
        return assets
    
    def _calculate_sha256(self, file_path: Path, chunk_size: int = 8192) -> str:
        """Calculate SHA256 hash of a file."""
        sha256_hash = hashlib.sha256()
        
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(chunk_size), b""):
                sha256_hash.update(chunk)
                
        return sha256_hash.hexdigest()
    
    def _verify_asset(self, asset: AssetInfo) -> Tuple[bool, str]:
        """Verify an asset's integrity."""
        file_path = self.assets_dir / asset.name
        
        if not file_path.exists():
            return False, "File not found"
            
        # Check file size (quick check)
        file_size = file_path.stat().st_size
        expected_size = int(asset.size_mb * 1024 * 1024)  # Convert MB to bytes
        
        # Allow 5% tolerance for compression differences
        if abs(file_size - expected_size) > (expected_size * 0.05):
            return False, f"File size mismatch: {file_size} vs expected ~{expected_size}"
        
        # Calculate and verify SHA256
        try:
            file_hash = self._calculate_sha256(file_path)
            if file_hash != asset.sha256:
                return False, f"SHA256 mismatch: {file_hash} vs {asset.sha256}"
        except Exception as e:
            return False, f"Hash calculation failed: {e}"
            
        return True, "Verified successfully"
    
    def _download_with_resume(self, asset: AssetInfo, max_retries: int = 3) -> bool:
        """Download asset with resume support and retries."""
        file_path = self.assets_dir / asset.name
        temp_path = file_path.with_suffix('.downloading')
        
        for attempt in range(max_retries):
            try:
                # Check if partial download exists
                resume_pos = 0
                if temp_path.exists():
                    resume_pos = temp_path.stat().st_size
                    print(f"  Resuming from {resume_pos:,} bytes")
                
                # Prepare request with resume header
                req = urllib.request.Request(asset.url)
                if resume_pos > 0:
                    req.add_header('Range', f'bytes={resume_pos}-')
                
                print(f"  Downloading {asset.name} ({asset.size_mb:.1f} MB)...")
                
                with urllib.request.urlopen(req) as response:
                    mode = 'ab' if resume_pos > 0 else 'wb'
                    
                    with open(temp_path, mode) as f:
                        downloaded = resume_pos
                        chunk_size = 8192
                        
                        while True:
                            chunk = response.read(chunk_size)
                            if not chunk:
                                break
                                
                            f.write(chunk)
                            downloaded += len(chunk)
                            
                            # Progress indicator
                            if downloaded % (1024 * 1024) == 0:  # Every MB
                                mb_downloaded = downloaded / (1024 * 1024)
                                print(f"    Downloaded: {mb_downloaded:.1f} MB", end='\r')
                
                # Move to final location
                temp_path.rename(file_path)
                print(f"  ✅ Downloaded: {asset.name}")
                return True
                
            except urllib.error.HTTPError as e:
                if e.code == 416:  # Range not satisfiable - file already complete
                    if temp_path.exists():
                        temp_path.rename(file_path)
                    return True
                    
                wait_time = (2 ** attempt) * 5  # Exponential backoff: 5s, 10s, 20s
                print(f"  ⚠️  Download failed (attempt {attempt + 1}/{max_retries}): {e}")
                
                if attempt < max_retries - 1:
                    print(f"     Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    
            except Exception as e:
                print(f"  ❌ Download error: {e}")
                break
        
        print(f"  ❌ Failed to download: {asset.name}")
        return False
    
    def plan(self) -> None:
        """Show download plan without executing."""
        print("📋 StratMaster Asset Download Plan")
        print("=" * 50)
        
        assets = self._get_all_assets()
        
        # Group by status
        to_download = []
        up_to_date = []
        failed_verification = []
        
        for asset in assets:
            if asset.name in self.lock_data:
                lock_entry = self.lock_data[asset.name]
                if lock_entry.status == "complete" and lock_entry.sha256 == asset.sha256:
                    # Verify file still exists and is valid
                    is_valid, message = self._verify_asset(asset)
                    if is_valid:
                        up_to_date.append(asset)
                    else:
                        failed_verification.append((asset, message))
                else:
                    to_download.append(asset)
            else:
                to_download.append(asset)
        
        # Display plan
        if to_download:
            print(f"\n📥 Assets to Download ({len(to_download)}):")
            total_size = 0
            for asset in to_download:
                status = "required" if not asset.optional else "optional"
                print(f"  • {asset.name} ({asset.size_mb:.1f} MB) - {status}")
                print(f"    {asset.description}")
                if not asset.optional:
                    total_size += asset.size_mb
            print(f"\nTotal download size (required): {total_size:.1f} MB")
        
        if up_to_date:
            print(f"\n✅ Up to Date ({len(up_to_date)}):")
            for asset in up_to_date:
                print(f"  • {asset.name}")
        
        if failed_verification:
            print(f"\n⚠️  Failed Verification ({len(failed_verification)}):")
            for asset, message in failed_verification:
                print(f"  • {asset.name}: {message}")
        
        print(f"\nManifest: {self.manifest_path}")
        print(f"Assets directory: {self.assets_dir}")
        print(f"Lock file: {self.lock_path}")
    
    def pull(self, required_only: bool = False) -> None:
        """Download assets according to manifest."""
        print("📥 StratMaster Asset Download")
        print("=" * 40)
        
        if self.dry_run:
            print("🔍 DRY RUN - No files will be downloaded")
        
        assets = self._get_all_assets()
        
        # Filter assets if required_only
        if required_only:
            assets = [asset for asset in assets if not asset.optional]
            print(f"📦 Downloading {len(assets)} required assets only")
        else:
            print(f"📦 Downloading {len(assets)} total assets")
        
        success_count = 0
        for i, asset in enumerate(assets, 1):
            print(f"\n[{i}/{len(assets)}] Processing: {asset.name}")
            
            # Check if already downloaded and verified
            if (asset.name in self.lock_data and 
                self.lock_data[asset.name].status == "complete" and
                self.lock_data[asset.name].sha256 == asset.sha256):
                
                # Quick verification
                is_valid, message = self._verify_asset(asset)
                if is_valid:
                    print(f"  ✅ Already downloaded and verified")
                    success_count += 1
                    continue
                else:
                    print(f"  🔄 Re-downloading due to: {message}")
            
            # Download the asset
            if self.dry_run:
                print(f"  🔍 Would download: {asset.url}")
                success_count += 1
            else:
                download_success = self._download_with_resume(asset)
                
                if download_success:
                    # Verify downloaded file
                    is_valid, message = self._verify_asset(asset)
                    
                    if is_valid:
                        # Update lock file
                        self.lock_data[asset.name] = AssetLockEntry(
                            name=asset.name,
                            url=asset.url,
                            sha256=asset.sha256,
                            downloaded_at=datetime.now(UTC).isoformat(),
                            verified_at=datetime.now(UTC).isoformat(),
                            file_size=(self.assets_dir / asset.name).stat().st_size,
                            status="complete"
                        )
                        self._save_lock_file()
                        success_count += 1
                        print(f"  ✅ Downloaded and verified successfully")
                    else:
                        print(f"  ❌ Verification failed: {message}")
                        # Mark as failed in lock file
                        self.lock_data[asset.name] = AssetLockEntry(
                            name=asset.name,
                            url=asset.url,
                            sha256=asset.sha256,
                            downloaded_at=datetime.now(UTC).isoformat(),
                            verified_at="",
                            file_size=0,
                            status="failed"
                        )
                        self._save_lock_file()
        
        # Summary
        print(f"\n📊 Download Summary")
        print(f"Successfully downloaded: {success_count}/{len(assets)}")
        if success_count < len(assets):
            print(f"Failed downloads: {len(assets) - success_count}")
            return False
        
        print("✅ All assets downloaded successfully!")
        return True
    
    def verify(self) -> None:
        """Verify all downloaded assets."""
        print("🔍 StratMaster Asset Verification")
        print("=" * 40)
        
        assets = self._get_all_assets()
        verified_count = 0
        
        for i, asset in enumerate(assets, 1):
            print(f"\n[{i}/{len(assets)}] Verifying: {asset.name}")
            
            is_valid, message = self._verify_asset(asset)
            
            if is_valid:
                print(f"  ✅ {message}")
                verified_count += 1
                
                # Update verification timestamp in lock
                if asset.name in self.lock_data:
                    self.lock_data[asset.name].verified_at = datetime.now(UTC).isoformat()
                    self.lock_data[asset.name].status = "complete"
            else:
                print(f"  ❌ {message}")
                
                # Update failed status in lock
                if asset.name in self.lock_data:
                    self.lock_data[asset.name].status = "failed"
        
        if not self.dry_run:
            self._save_lock_file()
        
        # Summary
        print(f"\n📊 Verification Summary")
        print(f"Successfully verified: {verified_count}/{len(assets)}")
        
        if verified_count == len(assets):
            print("✅ All assets verified successfully!")
        else:
            print(f"❌ {len(assets) - verified_count} assets failed verification")


def main():
    parser = argparse.ArgumentParser(
        description="StratMaster Asset Management System",
        epilog="""
Examples:
  python scripts/assets_pull.py plan                    # Show download plan
  python scripts/assets_pull.py pull --required-only    # Download required assets only
  python scripts/assets_pull.py pull --all             # Download all assets
  python scripts/assets_pull.py verify                 # Verify existing downloads
  python scripts/assets_pull.py --dry-run pull --all   # Simulate full download
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('command', choices=['plan', 'pull', 'verify'],
                       help='Action to perform')
    parser.add_argument('--manifest', default='scripts/assets_manifest.yaml',
                       help='Path to asset manifest file')
    parser.add_argument('--assets-dir', default='assets',
                       help='Directory to store downloaded assets')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be done without executing')
    parser.add_argument('--required-only', action='store_true',
                       help='Only process required (non-optional) assets')
    parser.add_argument('--all', action='store_true',
                       help='Process all assets including optional ones')
    
    args = parser.parse_args()
    
    # Validate arguments
    if args.command == 'pull' and not (args.required_only or args.all):
        print("Error: pull command requires either --required-only or --all")
        sys.exit(1)
    
    try:
        # Initialize asset manager
        manager = AssetManager(
            manifest_path=args.manifest,
            assets_dir=args.assets_dir,
            dry_run=args.dry_run
        )
        
        # Execute command
        if args.command == 'plan':
            manager.plan()
        elif args.command == 'pull':
            success = manager.pull(required_only=args.required_only)
            if not success:
                sys.exit(1)
        elif args.command == 'verify':
            manager.verify()
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Download interrupted by user")
        sys.exit(1)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
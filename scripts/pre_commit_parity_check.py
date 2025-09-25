#!/usr/bin/env python3
"""
Pre-commit Code-Documentation Parity Hook
Ensures code-documentation sync before commits
"""

import sys
import subprocess
from pathlib import Path

def main():
    """Run pre-commit parity checks."""
    print("🔍 Running code-documentation parity checks...")
    
    # Change to project root
    project_root = Path(__file__).parent.parent
    
    try:
        # Run the developer sync helper in quick mode
        result = subprocess.run([
            'python3', str(project_root / 'scripts' / 'dev_sync_helper.py'),
            '--mode', 'quick',
            '--quiet'
        ], cwd=project_root)
        
        if result.returncode == 0:
            print("✅ Code-documentation parity checks passed")
            return 0
        elif result.returncode == 1:
            print("⚠️ Code-documentation parity issues found (non-critical)")
            print("   Run: python scripts/dev_sync_helper.py --mode comprehensive")
            print("   Consider fixing issues before committing")
            return 0  # Allow commit but warn
        else:
            print("❌ Critical code-documentation parity issues found")
            print("   Run: python scripts/dev_sync_helper.py --mode comprehensive")
            print("   Please fix critical issues before committing")
            return 1  # Block commit
            
    except Exception as e:
        print(f"❌ Error running parity checks: {e}")
        return 0  # Allow commit if check fails

if __name__ == "__main__":
    sys.exit(main())
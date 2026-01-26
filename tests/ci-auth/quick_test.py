#!/usr/bin/env python3
"""
Quick test runner to verify the CI system is working.
"""

import asyncio
import sys
from pathlib import Path

# Add the parent directory to path so we can import our modules
sys.path.append(str(Path(__file__).parent))

from phase1_contract_validator import ContractValidator

def main():
    """Quick validation that our test system is working."""
    project_root = Path(__file__).parent.parent.parent
    
    print("🔍 Running quick CI system validation...")
    print(f"Project root: {project_root}")
    
    # Test Phase 1 - Contract Validation (doesn't require Docker)
    validator = ContractValidator(str(project_root))
    
    try:
        # Just test that the validator can load and run
        # Don't require all validations to pass for this quick test
        success = validator.validate_environment_variables()
        
        print(f"✅ Contract validator: {'WORKING' if success else 'LOADED (with warnings)'}")
        print("🎉 CI system appears to be correctly installed!")
        print("\nTo run full tests:")
        print(f"  cd {Path(__file__).parent}")
        print(f"  ./run_auth_tests.sh --help")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
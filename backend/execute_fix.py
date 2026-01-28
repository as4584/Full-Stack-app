#!/usr/bin/env python3
"""
Execute Schema Fix and Business Seeding
"""

import subprocess
import sys
import time

def run_command(command, description):
    print(f"\n🔄 {description}")
    print(f"Command: {command}")
    
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ SUCCESS")
            if result.stdout.strip():
                print("Output:", result.stdout.strip())
        else:
            print(f"❌ FAILED (exit code: {result.returncode})")
            if result.stderr.strip():
                print("Error:", result.stderr.strip())
            return False
            
    except Exception as e:
        print(f"❌ EXCEPTION: {e}")
        return False
    
    return True

def main():
    print("🔧 AI Receptionist Schema Fix - Automated Execution")
    print("=" * 60)
    
    # Change to backend directory
    backend_dir = "/home/lex/lexmakesit/backend"
    
    # Step 1: Apply migration
    if not run_command(f"cd {backend_dir} && docker compose exec app python -m alembic upgrade head", "Applying database migration"):
        sys.exit(1)
    
    time.sleep(2)
    
    # Step 2: Run schema fix and seeding
    if not run_command(f"cd {backend_dir} && docker compose exec app python fix_schema_and_seed.py", "Running schema fix and business seeding"):
        sys.exit(1)
    
    time.sleep(2)
    
    # Step 3: Verify API health
    if not run_command(f"cd {backend_dir} && curl -s http://localhost:8002/health", "Verifying API health"):
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("🎉 SCHEMA FIX AND SEEDING COMPLETED SUCCESSFULLY!")
    print("=" * 60)

if __name__ == "__main__":
    main()
#!/bin/bash
# Fix user password on production server
# Run with: bash fix_password_remote.sh

set -e

echo "=== Checking production database users ==="

ssh droplet << 'EOF'
docker exec ai_receptionist-app-1 python3 << 'PYTHON'
from ai_receptionist.db.database import SessionLocal
from ai_receptionist.models.user import User
from ai_receptionist.core.auth import get_password_hash, verify_password, create_access_token
from sqlalchemy import func

TARGET_EMAIL = "thegamermasterninja@gmail.com"
NEW_PASSWORD = "Alexander1221"

db = SessionLocal()

# List all users first
print("=" * 60)
print("ALL USERS IN PRODUCTION DATABASE:")
print("=" * 60)
users = db.query(User).all()
for u in users:
    print(f"  ID: {u.id}, Email: {u.email}, Name: {u.full_name}")
print()

# Find target user
user = db.query(User).filter(User.email == TARGET_EMAIL).first()

if not user:
    print(f"USER NOT FOUND: {TARGET_EMAIL}")
    print("Cannot proceed - user must exist first")
else:
    print(f"USER FOUND: {user.email} (ID: {user.id})")
    
    # Update password
    new_hash = get_password_hash(NEW_PASSWORD)
    user.password_hash = new_hash
    db.commit()
    
    # Verify
    db.refresh(user)
    verified = verify_password(NEW_PASSWORD, user.password_hash)
    print(f"Password updated and verified: {verified}")
    
    if verified:
        print()
        print("=" * 60)
        print("SUCCESS!")
        print(f"  Email: {TARGET_EMAIL}")
        print(f"  Password: {NEW_PASSWORD}")
        print(f"  User ID: {user.id}")
        print("=" * 60)

db.close()
PYTHON
EOF

echo "Done!"

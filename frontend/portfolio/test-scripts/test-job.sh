#!/bin/bash
# Test the "test" job from GitHub Actions locally
# This script replicates the exact steps from the workflow

set -e
echo "🧪 Testing GitHub Actions 'test' job locally..."

# Setup Python environment
echo "📦 Setting up Python 3.11..."
python3 --version

# Install dependencies exactly like in CI
echo "📦 Installing dependencies..."
python3 -m pip install --upgrade pip
pip install -r requirements.txt
pip install pytest pytest-asyncio httpx

# Run linting and auto-fix formatting
echo "🔧 Running linting and formatting..."
pip install flake8 black isort

# Auto-fix formatting issues
echo "🔧 Auto-formatting code with black..."
black . --verbose

echo "🔧 Auto-sorting imports with isort..."
isort . --verbose

echo "🔍 Running flake8 for code quality..."
# Stop the build if there are Python syntax errors or undefined names
flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics --exclude=venv,__pycache__,.git

# Run flake8 with warnings (but don't fail the build)
echo "📊 Code quality report:"
flake8 . --count --statistics --exclude=venv,__pycache__,.git --exit-zero || true

echo "✅ Linting completed successfully"

# Run security checks
echo "🔍 Running security checks..."
pip install bandit safety
# Check for security issues (allow to continue on warnings)
echo "🔍 Running security checks..."
bandit -r . -x ./venv,./node_modules --severity-level medium || true
# Check for known security vulnerabilities
safety check --ignore 70612 || true  # Ignore specific non-critical issues
echo "✅ Security checks completed"

# Run tests
echo "🧪 Running tests..."
# Set test environment variables
export DATABASE_URL="sqlite:///./test.db"
export PRODUCTION="false"
export SECRET_KEY="test-secret-key-for-ci"
export ALLOWED_ORIGINS="*"
export TRUSTED_HOSTS="*"
export RATE_LIMIT_PER_MINUTE="1000"
export SMTP_HOST="smtp.gmail.com"
export SMTP_PORT="587"
export SMTP_USER=""
export SMTP_PASSWORD=""

# Run tests if they exist
if [ -f "test_main.py" ]; then
  echo "🧪 Running pytest..."
  python3 -m pytest test_main.py -v --tb=short
else
  echo "🧪 Running basic import test..."
  python3 -c "import main; print('✅ Main module imports successfully')"
fi

echo "🎉 Test job completed successfully!"
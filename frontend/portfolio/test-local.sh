#!/bin/bash
# 🧪 Quick GitHub Actions Testing Script
# Run this to test your workflow jobs locally before pushing

set -e

echo "🚀 GitHub Actions Local Testing Suite"
echo "======================================"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

print_status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[⚠]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

echo ""
echo "📋 Available tests:"
echo "1. Quick validation (format + lint + import)"
echo "2. Full test job simulation"
echo "3. Build job simulation"
echo "4. Deploy job simulation" 
echo "5. Run all tests"
echo "6. View last test results"
echo ""

read -p "Select test [1-6]: " choice

case $choice in
    1)
        echo "🔍 Running quick validation..."
        echo "Formatting code..."
        python3 -m pip install black isort flake8 --quiet
        black . --quiet
        isort . --quiet
        
        echo "Checking critical linting..."
        if flake8 . --count --select=E9,F63,F7,F82 --exclude=venv,__pycache__,.git --statistics; then
            print_status "No critical linting errors"
        else
            print_error "Critical linting errors found"
            exit 1
        fi
        
        echo "Testing module import..."
        export DATABASE_URL="sqlite:///./test.db"
        export PRODUCTION="false" 
        export SECRET_KEY="test-key"
        export ALLOWED_ORIGINS="*"
        
        if python3 -c "import main; print('✓ Import successful')"; then
            print_status "Quick validation passed!"
        else
            print_error "Module import failed"
            exit 1
        fi
        ;;
        
    2)
        echo "🧪 Running full test job..."
        ./test-scripts/test-job.sh
        ;;
        
    3)
        echo "🏗️ Running build job..."
        if command -v docker &> /dev/null; then
            ./test-scripts/build-job.sh
        else
            print_warning "Docker not available, using fallback test"
            ./test-scripts/build-job-no-docker.sh
        fi
        ;;
        
    4)
        echo "🚀 Running deploy job..."
        ./test-scripts/deploy-job.sh
        ;;
        
    5)
        echo "🔄 Running all tests..."
        
        echo "1/4 - Quick validation..."
        if ./test-local.sh 1; then
            print_status "Quick validation passed"
        else
            print_error "Quick validation failed"
        fi
        
        echo "2/4 - Test job..."
        if ./test-scripts/test-job.sh; then
            print_status "Test job simulation completed"
        else
            print_warning "Test job had some issues (check output)"
        fi
        
        echo "3/4 - Build job..."
        if command -v docker &> /dev/null; then
            if ./test-scripts/build-job.sh; then
                print_status "Build job passed"
            else
                print_error "Build job failed"
            fi
        else
            if ./test-scripts/build-job-no-docker.sh; then
                print_status "Build job simulation passed"
            else
                print_error "Build job simulation failed"
            fi
        fi
        
        echo "4/4 - Deploy job..."
        if ./test-scripts/deploy-job.sh; then
            print_status "Deploy job simulation passed"
        else
            print_error "Deploy job simulation failed"
        fi
        
        echo ""
        print_status "All tests completed! Check TEST_RESULTS.md for detailed results."
        ;;
        
    6)
        echo "📄 Last test results:"
        if [ -f "TEST_RESULTS.md" ]; then
            head -30 TEST_RESULTS.md
            echo ""
            echo "💡 Full results in TEST_RESULTS.md"
        else
            print_warning "No test results found. Run tests first."
        fi
        ;;
        
    *)
        print_error "Invalid choice"
        exit 1
        ;;
esac

echo ""
echo "🎯 Testing complete!"
echo "💡 If all tests pass, your workflow should work on GitHub Actions"
echo "📋 Don't forget to configure repository secrets before pushing"
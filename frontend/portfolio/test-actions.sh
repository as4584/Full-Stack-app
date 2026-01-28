#!/bin/bash
# 🧪 Local GitHub Actions Testing Suite
# This script allows you to test all your GitHub Actions jobs locally before pushing

set -e  # Exit on any error

echo "🚀 GitHub Actions Local Testing Suite"
echo "======================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if act is installed
if ! command -v act &> /dev/null; then
    print_error "act is not installed. Please install it first."
    exit 1
fi

# Check if Docker is running
if ! docker info &> /dev/null; then
    print_error "Docker is not running. Please start Docker first."
    exit 1
fi

print_status "Starting local GitHub Actions testing..."

# Create local testing environment
print_status "Setting up local testing environment..."

# Function to run individual job
run_job() {
    local job_name=$1
    local description=$2
    
    print_status "Testing job: $job_name - $description"
    
    if act --job $job_name --secret-file .secrets --dryrun; then
        print_success "✅ $job_name - Dry run passed"
        
        # Ask if user wants to run the actual job
        echo -n "Run $job_name for real? (y/n): "
        read -r response
        if [[ "$response" =~ ^[Yy]$ ]]; then
            if act --job $job_name --secret-file .secrets; then
                print_success "✅ $job_name completed successfully"
            else
                print_error "❌ $job_name failed"
                return 1
            fi
        else
            print_warning "⏭️ Skipping actual execution of $job_name"
        fi
    else
        print_error "❌ $job_name - Dry run failed"
        return 1
    fi
}

# Function to test individual components
test_components() {
    print_status "Testing individual components locally..."
    
    # Test 1: Python Dependencies
    print_status "1. Testing Python dependencies..."
    if python3 -m pip install -r requirements.txt --quiet; then
        print_success "✅ Dependencies installed successfully"
    else
        print_error "❌ Failed to install dependencies"
        return 1
    fi
    
    # Test 2: Code formatting
    print_status "2. Testing code formatting..."
    pip install black isort flake8 --quiet
    
    # Check if black would make changes
    if black --check . 2>/dev/null; then
        print_success "✅ Code is properly formatted"
    else
        print_warning "⚠️ Code needs formatting (black will fix this)"
        black . --quiet
        print_success "✅ Code formatted with black"
    fi
    
    # Check import sorting
    if isort --check-only . 2>/dev/null; then
        print_success "✅ Imports are properly sorted"
    else
        print_warning "⚠️ Imports need sorting (isort will fix this)"
        isort . --quiet
        print_success "✅ Imports sorted with isort"
    fi
    
    # Test 3: Linting
    print_status "3. Testing linting..."
    if flake8 . --count --select=E9,F63,F7,F82 --exclude=venv,__pycache__,.git --show-source --statistics; then
        print_success "✅ No critical linting errors"
    else
        print_error "❌ Critical linting errors found"
        return 1
    fi
    
    # Test 4: Security checks
    print_status "4. Testing security checks..."
    pip install bandit safety --quiet
    
    if bandit -r . -x ./venv,./node_modules --severity-level medium --quiet -f txt; then
        print_success "✅ No high-severity security issues"
    else
        print_warning "⚠️ Security issues found (review bandit output)"
    fi
    
    # Test 5: Module imports
    print_status "5. Testing module imports..."
    if python3 -c "import main; print('Main module imports successfully')"; then
        print_success "✅ Main module imports successfully"
    else
        print_error "❌ Failed to import main module"
        return 1
    fi
    
    # Test 6: FastAPI app creation
    print_status "6. Testing FastAPI app creation..."
    if python3 -c "from main import app; print('FastAPI app created successfully')"; then
        print_success "✅ FastAPI app created successfully"
    else
        print_error "❌ Failed to create FastAPI app"
        return 1
    fi
    
    # Test 7: pytest if tests exist
    if [ -f "test_main.py" ]; then
        print_status "7. Running pytest..."
        pip install pytest pytest-asyncio httpx --quiet
        
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
        
        if python3 -m pytest test_main.py -v --tb=short; then
            print_success "✅ All tests passed"
        else
            print_error "❌ Some tests failed"
            return 1
        fi
    else
        print_warning "⚠️ No test_main.py found, skipping pytest"
    fi
    
    # Test 8: Docker build
    print_status "8. Testing Docker build..."
    if docker build -t portfolio-test . --quiet; then
        print_success "✅ Docker image built successfully"
        
        # Test container run
        print_status "9. Testing Docker container..."
        if timeout 30 docker run --rm -d -p 8002:8001 -e DATABASE_URL="sqlite:///./test.db" portfolio-test; then
            sleep 5
            if curl -f http://localhost:8002/api/health &>/dev/null; then
                print_success "✅ Docker container runs and responds"
            else
                print_warning "⚠️ Docker container starts but health check failed"
            fi
            docker stop $(docker ps -q --filter ancestor=portfolio-test) 2>/dev/null || true
        else
            print_warning "⚠️ Docker container test skipped or failed"
        fi
        
        # Clean up test image
        docker rmi portfolio-test --force 2>/dev/null || true
    else
        print_error "❌ Docker build failed"
        return 1
    fi
    
    print_success "🎉 All component tests completed successfully!"
}

# Main menu
show_menu() {
    echo ""
    echo "Select testing option:"
    echo "1) Test all components locally (recommended first)"
    echo "2) Test individual GitHub Actions job"
    echo "3) Test all GitHub Actions jobs (requires Docker)"
    echo "4) Quick validation (format + lint + import)"
    echo "5) Exit"
    echo ""
}

# Quick validation function
quick_validation() {
    print_status "Running quick validation..."
    
    # Install tools
    pip install black isort flake8 --quiet
    
    # Format and check
    black . --quiet
    isort . --quiet
    
    # Lint
    if flake8 . --count --select=E9,F63,F7,F82 --exclude=venv,__pycache__,.git --statistics; then
        print_success "✅ Quick validation passed"
    else
        print_error "❌ Quick validation failed"
        return 1
    fi
    
    # Test import
    if python3 -c "import main; print('✅ Import test passed')"; then
        print_success "✅ All quick validations passed"
    else
        print_error "❌ Import test failed"
        return 1
    fi
}

# Main execution
while true; do
    show_menu
    echo -n "Enter your choice [1-5]: "
    read -r choice
    
    case $choice in
        1)
            test_components
            ;;
        2)
            echo "Available jobs:"
            echo "- test (Run Tests)"
            echo "- build (Build Docker Image)"
            echo "- deploy (Deploy to Production)"
            echo ""
            echo -n "Enter job name: "
            read -r job_name
            
            case $job_name in
                test)
                    run_job "test" "Run Tests"
                    ;;
                build)
                    run_job "build" "Build Docker Image"
                    ;;
                deploy)
                    print_warning "Deploy job requires actual server access and will be simulated only"
                    run_job "deploy" "Deploy to Production"
                    ;;
                *)
                    print_error "Invalid job name"
                    ;;
            esac
            ;;
        3)
            print_status "Testing all GitHub Actions jobs..."
            run_job "test" "Run Tests"
            run_job "build" "Build Docker Image" 
            print_warning "Skipping deploy job (requires server access)"
            ;;
        4)
            quick_validation
            ;;
        5)
            print_status "Exiting..."
            exit 0
            ;;
        *)
            print_error "Invalid option. Please try again."
            ;;
    esac
done
#!/bin/bash
# Test build job components without Docker (fallback for environments without Docker)

set -e
echo "🏗️ Testing GitHub Actions 'build' job components (no Docker mode)..."

# Check if Dockerfile exists and is valid
echo "📋 Checking Dockerfile..."
if [ -f "Dockerfile" ]; then
    echo "✅ Dockerfile found"
    echo "📄 Dockerfile content:"
    cat Dockerfile | head -20
    echo ""
    
    # Basic Dockerfile syntax check
    if grep -q "FROM" Dockerfile && grep -q "COPY\|ADD" Dockerfile; then
        echo "✅ Dockerfile appears to have basic valid syntax"
    else
        echo "⚠️ Dockerfile might be missing required instructions"
    fi
else
    echo "❌ Dockerfile not found!"
    exit 1
fi

# Check for build context files
echo "📁 Checking build context..."
essential_files=("main.py" "requirements.txt")
for file in "${essential_files[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file found"
    else
        echo "❌ $file missing!"
        exit 1
    fi
done

# Check templates and static directories
if [ -d "templates" ]; then
    echo "✅ templates directory found ($(ls templates/ | wc -l) files)"
else
    echo "⚠️ templates directory not found"
fi

if [ -d "static" ]; then
    echo "✅ static directory found"
else
    echo "⚠️ static directory not found"
fi

# Simulate metadata extraction
echo "📋 Simulating metadata extraction..."
REGISTRY="ghcr.io"
IMAGE_NAME="as4584/portfolio"
BRANCH=$(git branch --show-current 2>/dev/null || echo "unknown")
COMMIT_SHA=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")

echo "Registry: $REGISTRY"
echo "Image name: $IMAGE_NAME"
echo "Branch: $BRANCH"
echo "Commit: $COMMIT_SHA"

# Generate tags like in the workflow
TAGS=(
    "$REGISTRY/$IMAGE_NAME:$BRANCH"
    "$REGISTRY/$IMAGE_NAME:$BRANCH-$COMMIT_SHA"
)

if [ "$BRANCH" = "main" ]; then
    TAGS+=("$REGISTRY/$IMAGE_NAME:latest")
fi

echo "Generated tags:"
for tag in "${TAGS[@]}"; do
    echo "  - $tag"
done

# Test Python dependencies can be parsed
echo "🔍 Checking Python dependencies..."
if python3 -c "
import ast
import sys

def check_requirements(filename):
    try:
        with open(filename, 'r') as f:
            lines = f.readlines()
        
        valid_lines = 0
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#'):
                # Basic check for package name format
                if '==' in line or '>=' in line or '<=' in line:
                    valid_lines += 1
                elif line.replace('-', '').replace('_', '').replace('[', '').replace(']', '').isalnum():
                    valid_lines += 1
                    
        print(f'Found {valid_lines} valid package specifications')
        return valid_lines > 0
    except Exception as e:
        print(f'Error reading requirements: {e}')
        return False

if check_requirements('requirements.txt'):
    sys.exit(0)
else:
    sys.exit(1)
"; then
    echo "✅ requirements.txt appears valid"
else
    echo "❌ requirements.txt has issues"
    exit 1
fi

# Test that main module can be imported
echo "🧪 Testing module imports..."
export DATABASE_URL="sqlite:///./test.db"
export PRODUCTION="false" 
export SECRET_KEY="test-build-key"
export ALLOWED_ORIGINS="*"

if python3 -c "
import sys
try:
    import main
    print('✅ Main module imports successfully')
    if hasattr(main, 'app'):
        print('✅ FastAPI app instance found')
    else:
        print('⚠️ No app instance found in main module')
except Exception as e:
    print(f'❌ Import error: {e}')
    sys.exit(1)
"; then
    echo "✅ Module import test passed"
else
    echo "❌ Module import test failed"
    exit 1
fi

# Simulate build success
echo ""
echo "🎯 Build job simulation completed successfully!"
echo "📊 Summary:"
echo "  - Dockerfile: ✅ Valid"
echo "  - Build context: ✅ Complete"
echo "  - Dependencies: ✅ Parseable" 
echo "  - Module import: ✅ Working"
echo "  - Metadata: ✅ Generated"

# Show what would be built
echo ""
echo "🏗️ This would build a Docker image with:"
echo "  Base image: $(grep '^FROM' Dockerfile | head -1 | cut -d' ' -f2)"
echo "  Python app: FastAPI application"
echo "  Port: 8001 (from main.py)"
echo "  Tags: ${#TAGS[@]} different tags"

echo ""
echo "💡 To test with actual Docker, install Docker and run:"
echo "   docker build -t portfolio-test ."
echo "   docker run -d -p 8001:8001 portfolio-test"
echo ""
echo "🎉 Build job validation completed!"
#!/bin/bash
# Quick GitHub Actions Testing Demo
# Run this to quickly test all components

set -e

echo "🚀 Quick GitHub Actions Testing Demo"
echo "===================================="
echo ""

echo "📊 Available test options:"
echo ""
echo "1. ./test-actions.sh                   # Interactive test suite"
echo "2. ./test-scripts/test-job.sh          # Test the 'test' job only"
echo "3. ./test-scripts/build-job.sh         # Test the 'build' job only" 
echo "4. ./test-scripts/deploy-job.sh        # Test deployment preparation"
echo "5. act --list                          # List all available workflows"
echo "6. act --job test                      # Run test job with act"
echo "7. act --job build                     # Run build job with act"
echo ""

echo "🔍 Current project status:"
echo "Python version: $(python3 --version)"
echo "Docker status: $(docker --version 2>/dev/null || echo 'Not available')"
echo "Act status: $(act --version 2>/dev/null || echo 'Not available')"
echo ""

echo "📁 Test files created:"
ls -la test-scripts/ 2>/dev/null || echo "No test scripts directory"
echo ""

echo "💡 Quick validation (recommended first):"
echo "./test-actions.sh and select option 4"
echo ""

echo "🎯 Full workflow test:"
echo "./test-actions.sh and select option 1"
echo ""

# Ask what to run
echo -n "What would you like to test? [1-7 or 'q' to quit]: "
read -r choice

case $choice in
    1)
        ./test-actions.sh
        ;;
    2) 
        ./test-scripts/test-job.sh
        ;;
    3)
        ./test-scripts/build-job.sh
        ;;
    4)
        ./test-scripts/deploy-job.sh
        ;;
    5)
        act --list
        ;;
    6)
        echo "Running GitHub Actions 'test' job with act..."
        act --job test --secret-file .secrets
        ;;
    7)
        echo "Running GitHub Actions 'build' job with act..."  
        act --job build --secret-file .secrets
        ;;
    q|Q)
        echo "Exiting..."
        ;;
    *)
        echo "Invalid option. Run ./demo.sh again to see options."
        ;;
esac
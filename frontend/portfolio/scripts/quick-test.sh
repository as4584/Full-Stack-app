#!/bin/bash

# Quick Test Runner
# Fast feedback loop for development
# Usage: ./scripts/quick-test.sh

set -e

echo "⚡ Quick Test Runner"
echo "==================="

# Quick syntax check
echo -n "Syntax: "
if python3 -m py_compile main.py 2>/dev/null; then
    echo "✅"
else
    echo "❌ Syntax error in main.py"
    exit 1
fi

# Quick test run
echo -n "Tests:  "
if python3 -m pytest test_main.py -q --tb=no >/dev/null 2>&1; then
    echo "✅ ($(python3 -m pytest test_main.py --collect-only -q 2>/dev/null | grep -c 'test_') tests)"
else
    echo "❌ Tests failed"
    echo ""
    echo "Run './scripts/pre-push-check.sh' for detailed errors"
    exit 1
fi

echo ""
echo "🚀 Ready for development!"
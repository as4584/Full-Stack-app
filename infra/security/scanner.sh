#!/bin/bash
set -e

# Security Scanner Script
# Usage: ./scanner.sh [path_to_repo] [--ci]

REPO_PATH=${1:-.}
CI_MODE=false

if [[ "$2" == "--ci" ]]; then
    CI_MODE=true
fi

echo "Starting Security Scan for: $REPO_PATH"

# 1. Python Dependency Scan
if [ -f "$REPO_PATH/requirements.txt" ] || [ -f "$REPO_PATH/pyproject.toml" ]; then
    echo "Detected Python project. Running pip-audit..."
    pip install pip-audit safety
    pip-audit -r "$REPO_PATH/requirements.txt" || {
        echo "CRITICAL: Vulnerable Python dependencies found!"
        if [ "$CI_MODE" = true ]; then exit 1; fi
    }
    safety check -r "$REPO_PATH/requirements.txt" || {
        echo "CRITICAL: Safety check failed!"
        if [ "$CI_MODE" = true ]; then exit 1; fi
    }
fi

# 2. Node.js Dependency Scan
if [ -f "$REPO_PATH/package.json" ]; then
    echo "Detected Node.js project. Running npm audit..."
    (cd "$REPO_PATH" && npm audit --production --audit-level=high) || {
        echo "CRITICAL: High severity Node.js vulnerabilities found!"
        if [ "$CI_MODE" = true ]; then exit 1; fi
    }
fi

# 3. Malware Scan (ClamAV)
# Only run if clamscan is installed
if command -v clamscan &> /dev/null; then
    echo "Running ClamAV Malware Scan..."
    clamscan -r --bell -i "$REPO_PATH" || {
        echo "WARNING: Malware detected!"
        if [ "$CI_MODE" = true ]; then exit 1; fi
    }
else
    echo "ClamAV not installed. Skipping malware scan."
fi

echo "Security Scan Completed Successfully."

#!/usr/bin/env bash
# =============================================================================
# AI Career & Interview Coach - Unix/macOS Launcher
# =============================================================================

set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

echo "======================================================="
echo "   🚀 AI Career & Interview Coach - Starting Up"
echo "======================================================="
echo ""

# Check Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed! Please install Node.js (v18+) from https://nodejs.org/"
    exit 1
fi

# Check Python
if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    echo "❌ Python 3 is not installed! Please install Python 3.10+ from https://python.org/"
    exit 1
fi

node scripts/run.js

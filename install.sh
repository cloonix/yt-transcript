#!/usr/bin/env bash
set -euo pipefail

REPO="https://github.com/cloonix/yt-transcript.git"
PACKAGE="git+${REPO}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

info() { echo -e "${BLUE}==>${NC} $1"; }
success() { echo -e "${GREEN}==>${NC} $1"; }
warn() { echo -e "${YELLOW}==>${NC} $1"; }
error() { echo -e "${RED}==>${NC} $1"; }

# Check if command exists
has() { command -v "$1" >/dev/null 2>&1; }

echo ""
echo -e "${BLUE}ytt${NC} - YouTube Transcript Tool"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Ensure Python 3.8+ is available
if ! has python3; then
    error "Python 3 is required but not found."
    echo "  Install Python 3.8+ and try again."
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
PYTHON_MAJOR=$(echo "$PYTHON_VERSION" | cut -d. -f1)
PYTHON_MINOR=$(echo "$PYTHON_VERSION" | cut -d. -f2)

if [[ "$PYTHON_MAJOR" -lt 3 ]] || [[ "$PYTHON_MAJOR" -eq 3 && "$PYTHON_MINOR" -lt 8 ]]; then
    error "Python 3.8+ is required. Found: Python $PYTHON_VERSION"
    exit 1
fi

info "Found Python $PYTHON_VERSION"

# Install using the best available method
if has pipx; then
    info "Installing with pipx..."
    if pipx list | grep -q "ytt"; then
        warn "ytt is already installed. Upgrading..."
        pipx upgrade ytt || pipx install --force "$PACKAGE"
    else
        pipx install "$PACKAGE"
    fi
    success "Installed with pipx"

elif has uv; then
    info "Installing with uv..."
    uv tool install "$PACKAGE"
    success "Installed with uv"

elif has pip3; then
    warn "pipx not found. Installing with pip3 --user (consider installing pipx for isolation)"
    pip3 install --user "$PACKAGE"
    success "Installed with pip3"

    # Check if ~/.local/bin is in PATH
    if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
        echo ""
        warn "~/.local/bin is not in your PATH"
        echo "  Add this to your shell config (.bashrc, .zshrc, etc.):"
        echo ""
        echo "    export PATH=\"\$HOME/.local/bin:\$PATH\""
        echo ""
    fi

elif has pip; then
    warn "pipx not found. Installing with pip --user (consider installing pipx for isolation)"
    pip install --user "$PACKAGE"
    success "Installed with pip"

else
    error "No package manager found. Install pipx, uv, or pip and try again."
    echo ""
    echo "  To install pipx:"
    echo "    brew install pipx     # macOS"
    echo "    apt install pipx      # Debian/Ubuntu"
    echo "    pip install --user pipx"
    echo ""
    exit 1
fi

echo ""
success "Installation complete!"
echo ""
echo "  Usage:"
echo "    ytt <youtube-url>              # output to stdout"
echo "    ytt <youtube-url> -o file.txt  # save to file"
echo "    ytt -l de <youtube-url>        # prefer German transcript"
echo ""
echo "  Try it:"
echo "    ytt dQw4w9WgXcQ | head -5"
echo ""

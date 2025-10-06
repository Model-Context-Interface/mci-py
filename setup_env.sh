#!/usr/bin/env bash
# setup_env.sh - Environment setup script for mci-py
# This script installs uv, Python, and project dependencies

set -euo pipefail  # Exit on error, unset variables, and pipeline failures
IFS=$'\n\t'        # Make word splitting more robust

echo "========================================"
echo "Setting up mci-py development environment"
echo "========================================"
echo

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Step 1: Install uv if not already installed
echo "Step 1: Checking for uv installation..."
if command_exists uv; then
    echo "✓ uv is already installed"
    uv --version
else
    echo "Installing uv..."
    
    # Detect OS
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        if command_exists brew; then
            echo "Using Homebrew to install uv..."
            brew update
            brew install uv
        else
            echo "Homebrew not found. Downloading uv installer script..."
            tmpfile=$(mktemp /tmp/uv-install.XXXXXX.sh)
            curl -LsSf https://astral.sh/uv/install.sh -o "$tmpfile"
            echo "WARNING: You are about to execute a script downloaded from https://astral.sh/uv/install.sh"
            echo "This can be risky if the source is compromised. Consider verifying the script before running."
            echo "Do you want to proceed and run the installer script? [y/N]"
            read -r confirm
            if [[ "$confirm" =~ ^[Yy]$ ]]; then
                sh "$tmpfile"
            else
                echo "Aborted. You can inspect the installer script at $tmpfile"
                exit 1
            fi
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        echo "Downloading uv installer script..."
        tmpfile=$(mktemp /tmp/uv-install.XXXXXX.sh)
        curl -LsSf https://astral.sh/uv/install.sh -o "$tmpfile"
        echo "WARNING: You are about to execute a script downloaded from https://astral.sh/uv/install.sh"
        echo "This can be risky if the source is compromised. Consider verifying the script before running."
        echo "Do you want to proceed and run the installer script? [y/N]"
        read -r confirm
        if [[ "$confirm" =~ ^[Yy]$ ]]; then
            sh "$tmpfile"
        else
            echo "Aborted. You can inspect the installer script at $tmpfile"
            exit 1
        fi
    else
        echo "Unsupported OS: $OSTYPE"
        echo "Please install uv manually from https://docs.astral.sh/uv/getting-started/installation/"
        exit 1
    fi
    
    # Source the shell configuration to make uv available
    if [ -f "$HOME/.cargo/env" ]; then
        source "$HOME/.cargo/env"
    fi
    
    # Add to PATH if not already there
    if [ -d "$HOME/.cargo/bin" ]; then
        export PATH="$HOME/.cargo/bin:$PATH"
    fi
    
    # Verify uv is now available
    if command_exists uv; then
        echo "✓ uv installed successfully"
        uv --version
    else
        echo "Warning: uv was installed but is not in PATH."
        echo "You may need to restart your shell or run: source \$HOME/.cargo/env"
        echo "Or add \$HOME/.cargo/bin to your PATH manually."
    fi
fi

echo

# Step 2: Install Python using uv
echo "Step 2: Installing Python 3.13 using uv..."
if command_exists uv; then
    uv python install 3.13
    echo "✓ Python 3.13 installed successfully"
else
    echo "Error: uv is not available. Please ensure the installation was successful."
    exit 1
fi

echo

# Step 3: Install project dependencies using make
echo "Step 3: Installing project dependencies..."
if [ -f "Makefile" ]; then
    make install
    echo "✓ Project dependencies installed successfully"
else
    echo "Error: Makefile not found. Are you in the correct directory?"
    exit 1
fi

echo
echo "========================================"
echo "Setup completed successfully!"
echo "========================================"
echo
echo "Next steps:"
echo "  - Run 'make' to sync, lint, and test"
echo "  - Run 'make test' to run tests"
echo "  - Run 'make lint' to run linting"
echo "  - See development.md for more information"
echo

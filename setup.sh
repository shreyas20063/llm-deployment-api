#!/bin/bash
# Quick Setup Script for LLM Deployment Project (Mac/Conda version)
# Usage: bash setup.sh

set -e  # Exit on error

echo "=========================================="
echo "LLM Deployment Project - Quick Setup"
echo "Mac/Conda Version"
echo "=========================================="
echo ""

# Check if conda is installed
if ! command -v conda &> /dev/null; then
    echo "❌ Conda is not installed."
    echo ""
    echo "Please install Miniconda or Anaconda:"
    echo "  Miniconda: https://docs.conda.io/en/latest/miniconda.html"
    echo "  Anaconda: https://www.anaconda.com/download"
    exit 1
fi

echo "✅ Conda found: $(conda --version)"

# Initialize conda for bash (if not already done)
if [ -f "$HOME/miniconda3/etc/profile.d/conda.sh" ]; then
    source "$HOME/miniconda3/etc/profile.d/conda.sh"
elif [ -f "$HOME/anaconda3/etc/profile.d/conda.sh" ]; then
    source "$HOME/anaconda3/etc/profile.d/conda.sh"
fi

# Create conda environment if it doesn't exist
ENV_NAME="llm-deploy"

if conda env list | grep -q "^${ENV_NAME} "; then
    echo "✅ Conda environment '$ENV_NAME' already exists"
else
    echo ""
    echo "Creating conda environment '$ENV_NAME'..."
    conda create -n $ENV_NAME python=3.11 -y
    echo "✅ Conda environment created"
fi

# Activate conda environment
echo ""
echo "Activating conda environment '$ENV_NAME'..."
conda activate $ENV_NAME
echo "✅ Environment activated"

# Install dependencies
echo ""
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
echo "✅ Dependencies installed"

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo ""
    echo "Creating .env file..."
    cp .env.example .env
    echo "✅ .env file created"
    echo ""
    echo "⚠️  IMPORTANT: Edit .env file with your actual credentials:"
    echo "   1. GITHUB_TOKEN"
    echo "   2. GITHUB_USERNAME"
    echo "   3. YOUR_SECRET (create a password)"
    echo "   4. AIPIPE_TOKEN (already filled in)"
    echo ""
    echo "Run: nano .env"
else
    echo "✅ .env file already exists"
fi

# Make test script executable
chmod +x test_api.py

echo ""
echo "=========================================="
echo "✅ Setup Complete!"
echo "=========================================="
echo ""
echo "To activate the environment in the future, run:"
echo "  conda activate $ENV_NAME"
echo ""
echo "Next steps:"
echo "1. Edit your .env file: nano .env"
echo "2. Start the server: python app.py"
echo "3. Test locally: python test_api.py"
echo "4. Deploy to Render/Railway (see DEPLOYMENT_GUIDE.md)"
echo ""
echo "For detailed instructions, read DEPLOYMENT_GUIDE.md"
echo ""
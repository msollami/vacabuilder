#!/bin/bash

# Vacation Builder Setup Script

echo "========================================="
echo "  Vacation Builder Setup"
echo "========================================="
echo ""

# Check Node.js
echo "Checking Node.js installation..."
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 16+ from https://nodejs.org"
    exit 1
fi
echo "✓ Node.js $(node --version) found"

# Check npm
if ! command -v npm &> /dev/null; then
    echo "❌ npm is not installed"
    exit 1
fi
echo "✓ npm $(npm --version) found"

# Check Python
echo ""
echo "Checking Python installation..."
if command -v python3 &> /dev/null; then
    PYTHON_CMD=python3
elif command -v python &> /dev/null; then
    PYTHON_CMD=python
else
    echo "❌ Python is not installed. Please install Python 3.8+ from https://python.org"
    exit 1
fi

PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | awk '{print $2}')
echo "✓ Python $PYTHON_VERSION found"

# Install Node dependencies
echo ""
echo "Installing Node.js dependencies..."
npm install
if [ $? -ne 0 ]; then
    echo "❌ Failed to install Node.js dependencies"
    exit 1
fi
echo "✓ Node.js dependencies installed"

# Set up Python environment
echo ""
echo "Setting up Python virtual environment..."
cd backend

if [ ! -d "venv" ]; then
    $PYTHON_CMD -m venv venv
    if [ $? -ne 0 ]; then
        echo "❌ Failed to create virtual environment"
        exit 1
    fi
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi

# Activate virtual environment
echo ""
echo "Installing Python dependencies (this may take several minutes)..."
source venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "❌ Failed to install Python dependencies"
    exit 1
fi
echo "✓ Python dependencies installed"

# Check for model
echo ""
echo "Checking for LLM model..."
if ls models/*.gguf 1> /dev/null 2>&1; then
    echo "✓ GGUF model found in models/"
    ls -lh models/*.gguf
else
    echo "⚠️  No GGUF model found in backend/models/"
    echo ""
    echo "Please download a model file. Recommended:"
    echo "  - Mistral 7B Instruct Q4_K_M (~4GB)"
    echo ""
    echo "Download from: https://huggingface.co/TheBloke"
    echo "Place the .gguf file in: backend/models/"
fi

# Create .env if it doesn't exist
if [ ! -f ".env" ]; then
    echo ""
    echo "Creating .env file from example..."
    cp .env.example .env
    echo "✓ .env file created. Edit it to add your API keys (optional)"
fi

cd ..

echo ""
echo "========================================="
echo "  Setup Complete!"
echo "========================================="
echo ""
echo "Next steps:"
echo "1. Download a GGUF model (if not done already)"
echo "2. (Optional) Add Google Places API key to backend/.env"
echo "3. Run: npm run dev"
echo ""
echo "Happy vacation planning! ✈️"

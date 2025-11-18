#!/bin/bash

# Vacation Builder - One Command Runner
# This script sets up and runs the entire application

set -e

echo "========================================="
echo "  🚀 Starting Vacation Builder"
echo "========================================="
echo ""

# Kill any existing processes on port 8000
echo "🧹 Cleaning up existing processes..."
lsof -ti:8000 | xargs kill -9 2>/dev/null || true
sleep 1

# Check if Node modules exist
if [ ! -d "node_modules" ]; then
    echo "📦 Installing Node.js dependencies..."
    npm install
fi

# Determine which Python to use
PYTHON_CMD=""
if command -v python3.12 &> /dev/null; then
    PYTHON_CMD="python3.12"
    PYTHON_VERSION=$(python3.12 --version 2>&1 | awk '{print $2}')
    echo "✓ Found Python 3.12: $PYTHON_VERSION"
elif command -v python3.11 &> /dev/null; then
    PYTHON_CMD="python3.11"
    PYTHON_VERSION=$(python3.11 --version 2>&1 | awk '{print $2}')
    echo "✓ Found Python 3.11: $PYTHON_VERSION"
elif command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

    if [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -ge 13 ]; then
        echo "⚠️  Warning: Python $PYTHON_VERSION detected"
        echo "Python 3.13 has compatibility issues with some packages."
        echo ""
        echo "Installing Python 3.12 (recommended)..."
        brew install python@3.12

        if command -v python3.12 &> /dev/null; then
            PYTHON_CMD="python3.12"
            echo "✓ Python 3.12 installed successfully"
        else
            echo "❌ Failed to install Python 3.12"
            echo "Please install manually: brew install python@3.12"
            exit 1
        fi
    else
        PYTHON_CMD="python3"
        echo "✓ Found Python $PYTHON_VERSION"
    fi
else
    echo "❌ Python 3 not found. Please install Python 3.11 or 3.12"
    exit 1
fi

# Setup Python environment
echo ""
echo "🐍 Setting up Python environment with $PYTHON_CMD..."

# Always recreate venv if fastapi isn't installed
cd backend
if [ ! -d "venv" ] || ! venv/bin/python -c "import fastapi" 2>/dev/null; then
    echo "Creating fresh virtual environment..."
    rm -rf venv
    $PYTHON_CMD -m venv venv

    source venv/bin/activate

    echo "Installing Python packages (this may take 5-10 minutes)..."
    pip install --upgrade pip --quiet

    # Install packages one by one for better error reporting
    echo "  - Installing FastAPI..."
    pip install "fastapi>=0.109.0" --quiet

    echo "  - Installing Uvicorn..."
    pip install "uvicorn[standard]>=0.27.0" --quiet

    echo "  - Installing llama-cpp-python (this takes the longest)..."
    pip install "llama-cpp-python>=0.2.27"

    echo "  - Installing remaining packages..."
    pip install -r requirements.txt --quiet

    if [ $? -ne 0 ]; then
        echo ""
        echo "❌ Failed to install Python dependencies"
        echo "Try manually:"
        echo "  cd backend"
        echo "  source venv/bin/activate"
        echo "  pip install -r requirements.txt"
        exit 1
    fi

    echo "✓ All Python packages installed"
else
    echo "✓ Python environment exists and has FastAPI installed"
fi

cd ..

# Check for model file
if ! ls backend/models/*.gguf 1> /dev/null 2>&1; then
    echo ""
    echo "⚠️  WARNING: No GGUF model found in backend/models/"
    echo ""
    echo "Download a model with:"
    echo "  cd backend/models"
    echo "  curl -L -O https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF/resolve/main/mistral-7b-instruct-v0.2.Q4_K_M.gguf"
    echo "  cd ../.."
    echo "⚠️  Continuing without model - some features may not work"
    echo ""
else
    MODEL_FILE=$(ls backend/models/*.gguf | head -1)
    MODEL_NAME=$(basename "$MODEL_FILE")
    MODEL_SIZE=$(ls -lh "$MODEL_FILE" | awk '{print $5}')
    echo "✓ Model found: $MODEL_NAME ($MODEL_SIZE)"
fi

# Create .env if it doesn't exist
if [ ! -f "backend/.env" ]; then
    cp backend/.env.example backend/.env
    echo "✓ Created .env file"
fi

echo ""
echo "========================================="
echo "  🎉 Starting Application"
echo "========================================="
echo ""
echo "Backend will start on: http://127.0.0.1:8000"
echo "Electron app will launch automatically"
echo ""
echo "Press Ctrl+C to stop"
echo ""

# Start the application
npm run dev

#!/bin/bash
echo "╔══════════════════════════════════════════╗"
echo "║  🌿 Green Campus Alert Map - Setup      ║"
echo "║  ENSEREDD - Batna, Algeria               ║"
echo "╚══════════════════════════════════════════╝"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 is not installed!"
    exit 1
fi

echo "✅ Python3 found: $(python3 --version)"

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install --upgrade pip
pip install -r backend/requirements.txt

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p backend/uploads
mkdir -p backend/ml_models
mkdir -p logs
mkdir -p ml_data

# Initialize database
echo "🗄️ Initializing database..."
cd backend
python3 -c "from database import init_db; init_db()"

# Train ML models
echo "🤖 Training ML models..."
python3 ml_module.py
cd ..

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║  ✅ Setup Complete!                      ║"
echo "║  Run: ./scripts/start.sh                 ║"
echo "╚══════════════════════════════════════════╝"
#!/bin/bash
echo "🌿 Starting Green Campus Alert Map..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

source venv/bin/activate

echo "🚀 Server: http://localhost:5000"
echo "📊 Database: backend/green_campus.db"
echo "📁 Uploads: backend/uploads/"
echo "📝 Logs: logs/app.log"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

cd backend
python3 app.py
#!/bin/bash
# ============================================================
# Start Script – Green Campus Alert Map
# ============================================================

set -e
GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'

echo -e "${GREEN}Starting Green Campus Alert Map...${NC}"

# Start MySQL
sudo systemctl start mysql 2>/dev/null || true

# Activate venv and start Flask
cd backend
source venv/bin/activate

echo -e "${GREEN}Starting Flask backend on port 5000...${NC}"
export FLASK_APP=app.py
export FLASK_ENV=development
python app.py &
FLASK_PID=$!

echo -e "${GREEN}Application running!${NC}"
echo -e "Backend:  ${YELLOW}http://localhost:5000${NC}"
echo -e "Frontend: ${YELLOW}http://localhost:5000${NC}"
echo ""
echo "Press Ctrl+C to stop..."

# Cleanup on exit
trap "echo 'Stopping...'; kill $FLASK_PID 2>/dev/null; exit" INT TERM
wait $FLASK_PID
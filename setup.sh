#!/bin/bash
# ============================================================
# Setup Script – Green Campus Alert Map
# ENREDD Batna, Algeria
# ============================================================

set -e
GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'

echo -e "${GREEN}╔════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  Green Campus Alert Map - ENREDD Batna     ║${NC}"
echo -e "${GREEN}║           Setup Script v1.0                ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════╝${NC}"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${YELLOW}Python3 not found. Installing...${NC}"
    sudo apt-get update && sudo apt-get install -y python3 python3-pip python3-venv
fi

# Check MySQL
if ! command -v mysql &> /dev/null; then
    echo -e "${YELLOW}MySQL not found. Installing...${NC}"
    sudo apt-get install -y mysql-server
    sudo systemctl start mysql
fi

echo -e "${GREEN}[1/6] Creating Python virtual environment...${NC}"
cd backend
python3 -m venv venv
source venv/bin/activate

echo -e "${GREEN}[2/6] Installing dependencies...${NC}"
pip install --upgrade pip
pip install -r requirements.txt

echo -e "${GREEN}[3/6] Creating directories...${NC}"
mkdir -p uploads logs ml/models

echo -e "${GREEN}[4/6] Setting up database...${NC}"
read -p "Enter MySQL root password: " MYSQL_PASS
mysql -u root -p"$MYSQL_PASS" < ../database/schema.sql
mysql -u root -p"$MYSQL_PASS" < ../database/seed.sql
echo "Database initialized!"

echo -e "${GREEN}[5/6] Creating .env file...${NC}"
cat > .env << EOF
FLASK_ENV=development
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
JWT_SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
DB_USER=root
DB_PASSWORD=$MYSQL_PASS
DB_HOST=localhost
DB_PORT=3306
DB_NAME=green_campus_db
DEBUG=True
EOF
echo ".env file created!"

echo -e "${GREEN}[6/6] Training ML models...${NC}"
python3 ml/train_model.py
echo "ML models trained!"

echo ""
echo -e "${GREEN}✅ Setup complete!${NC}"
echo -e "Run: ${YELLOW}./scripts/start.sh${NC} to launch the application"
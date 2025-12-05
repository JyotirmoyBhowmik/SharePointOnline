#!/bin/bash
#
# SharePoint Governance Platform - Linux/Unix Deployment Script
# ==============================================================
#
# Author: Jyotirmoy Bhowmik
# Email: jyotirmoy.bhowmik@company.com
# Version: 3.0.0
# Created: 2025
# Last Modified: December 5, 2025
#
# Description:
#   Automated deployment script for Linux/Unix systems.
#   Checks prerequisites, installs Docker if needed, configures environment,
#   builds containers, starts services, and verifies deployment.
#
#   This script performs the following steps:
#   1. Check prerequisites (Docker, Docker Compose, Git)
#   2. Navigate to project directory
#   3. Configure environment variables (.env file)
#   4. Build Docker images
#   5. Start all services (PostgreSQL, Redis, Backend, Frontend)
#   6. Wait for services to be ready
#   7. Run database migrations
#   8. Verify deployment health
#
# Requirements:
#   - Ubuntu 20.04+ / Debian 11+ / CentOS 8+ / RHEL 8+
#   - 4GB RAM minimum, 8GB recommended
#   - 20GB disk space
#   - Internet connection for Docker image pulls
#   - Sudo/root access for Docker installation
#
# Usage:
#   chmod +x deploy.sh
#   ./deploy.sh
#
# Maintained by: Jyotirmoy Bhowmik
# ==============================================================

set -e  # Exit immediately if any command fails

echo "=========================================="
echo "SharePoint Governance Platform Deployment"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Step 1: Check Prerequisites
echo "Step 1: Checking prerequisites..."
echo "--------------------------------"

# Check Docker
if command_exists docker; then
    DOCKER_VERSION=$(docker --version)
    echo -e "${GREEN}✓${NC} Docker installed: $DOCKER_VERSION"
else
    echo -e "${RED}✗${NC} Docker not installed"
    echo "Installing Docker..."
    
    # Install Docker (Ubuntu/Debian)
    sudo apt-get update
    sudo apt-get install -y \
        ca-certificates \
        curl \
        gnupg \
        lsb-release
    
    sudo mkdir -p /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    
    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
      $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    
    sudo apt-get update
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    
    # Add current user to docker group
    sudo usermod -aG docker $USER
    echo -e "${GREEN}✓${NC} Docker installed successfully"
    echo -e "${YELLOW}⚠${NC}  Please log out and log back in for docker group to take effect"
fi

# Check Docker Compose
if command_exists docker-compose || docker compose version >/dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Docker Compose installed"
else
    echo -e "${RED}✗${NC} Docker Compose not installed"
    echo "Installing Docker Compose..."
    sudo curl -L "https://github.com/docker/compose/releases/download/v2.23.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    echo -e "${GREEN}✓${NC} Docker Compose installed"
fi

# Check Git
if command_exists git; then
    echo -e "${GREEN}✓${NC} Git installed: $(git --version)"
else
    echo -e "${RED}✗${NC} Git not installed"
    sudo apt-get install -y git
    echo -e "${GREEN}✓${NC} Git installed"
fi

# Check Node.js (for frontend development)
if command_exists node; then
    echo -e "${GREEN}✓${NC} Node.js installed: $(node --version)"
else
    echo -e "${YELLOW}⚠${NC}  Node.js not installed (optional for frontend development)"
    echo "Installing Node.js..."
    curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
    sudo apt-get install -y nodejs
    echo -e "${GREEN}✓${NC} Node.js installed: $(node --version)"
fi

echo ""
echo "Step 2: Navigate to project directory"
echo "--------------------------------------"
cd /home/genai/Documents/SharePointOnline/sharepoint-governance-platform
echo "Current directory: $(pwd)"

echo ""
echo "Step 3: Configure environment variables"
echo "----------------------------------------"
if [ ! -f .env ]; then
    echo "Creating .env from .env.example..."
    cp .env.example .env
    echo -e "${YELLOW}⚠${NC}  IMPORTANT: Edit .env file with your credentials:"
    echo "   - Microsoft Graph API credentials"
    echo "   - PostgreSQL password"
    echo "   - JWT secrets"
    echo "   - AD/LDAP settings"
    echo ""
    echo "Press ENTER to edit .env file now, or Ctrl+C to edit later"
    read
    ${EDITOR:-nano} .env
else
    echo -e "${GREEN}✓${NC} .env file already exists"
fi

echo ""
echo "Step 4: Build Docker images"
echo "----------------------------"
docker-compose build

echo ""
echo "Step 5: Start services"
echo "----------------------"
docker-compose up -d

echo ""
echo "Step 6: Wait for services to be ready"
echo "--------------------------------------"
echo "Waiting for PostgreSQL..."
sleep 10
until docker-compose exec -T postgres pg_isready -U admin; do
    echo "Waiting for PostgreSQL to be ready..."
    sleep 2
done
echo -e "${GREEN}✓${NC} PostgreSQL is ready"

echo "Waiting for Redis..."
until docker-compose exec -T redis redis-cli ping; do
    echo "Waiting for Redis to be ready..."
    sleep 2
done
echo -e "${GREEN}✓${NC} Redis is ready"

echo ""
echo "Step 7: Run database migrations"
echo "--------------------------------"
docker-compose exec backend alembic upgrade head
echo -e "${GREEN}✓${NC} Database migrations complete"

echo ""
echo "Step 8: Verify deployment"
echo "-------------------------"
echo "Checking service health..."
docker-compose ps

echo ""
echo "Testing backend health endpoint..."
HEALTH_CHECK=$(curl -s http://localhost:8000/health | jq -r '.status' 2>/dev/null || echo "unhealthy")
if [ "$HEALTH_CHECK" = "healthy" ]; then
    echo -e "${GREEN}✓${NC} Backend is healthy"
else
    echo -e "${RED}✗${NC} Backend health check failed"
fi

echo ""
echo "=========================================="
echo "Deployment Complete!"
echo "=========================================="
echo ""
echo "Access the platform:"
echo "  • Frontend:    http://localhost:3000"
echo "  • Backend:     http://localhost:8000"
echo "  • API Docs:    http://localhost:8000/api/v1/docs"
echo "  • Health:      http://localhost:8000/health"
echo ""
echo "Next steps:"
echo "  1. Login with your AD credentials"
echo "  2. Trigger site discovery: POST /api/v1/sites/discover"
echo "  3. View documentation in QUICKSTART.md"
echo "  4. Run tests: See TESTING_GUIDE.md"
echo ""
echo "To stop the platform:"
echo "  docker-compose down"
echo ""
echo "To view logs:"
echo "  docker-compose logs -f"
echo ""

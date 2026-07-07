#!/bin/bash
# Project verification script
# Run this to verify all components are in place

echo "🔍 Checking URL Shortener Project Structure..."
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

check_file() {
    if [ -f "$1" ]; then
        echo -e "${GREEN}✓${NC} $1"
        return 0
    else
        echo -e "${RED}✗${NC} $1 (MISSING)"
        return 1
    fi
}

check_dir() {
    if [ -d "$1" ]; then
        echo -e "${GREEN}✓${NC} $1/"
        return 0
    else
        echo -e "${RED}✗${NC} $1/ (MISSING)"
        return 1
    fi
}

echo "📄 Documentation"
check_file "README.md"
check_file "QUICKSTART.md"
check_file "ARCHITECTURE.md"
check_file "SYSTEM_DESIGN.md"
check_file "PROJECT_SUMMARY.md"

echo ""
echo "🔧 Configuration"
check_file "requirements.txt"
check_file ".env"
check_file ".gitignore"
check_file "Dockerfile"
check_file "docker-compose.yml"
check_file "conftest.py"

echo ""
echo "🏗️ Core Application (app/)"
check_dir "app"
check_file "app/__init__.py"
check_file "app/main.py"

echo ""
echo "🌍 Core Layer (app/core/)"
check_dir "app/core"
check_file "app/core/__init__.py"
check_file "app/core/config.py"
check_file "app/core/security.py"
check_file "app/core/logging.py"
check_file "app/core/exceptions.py"

echo ""
echo "🎯 Domain Layer (app/domain/)"
check_dir "app/domain"
check_dir "app/domain/entities"
check_dir "app/domain/repositories"
check_file "app/domain/__init__.py"
check_file "app/domain/entities/__init__.py"
check_file "app/domain/repositories/__init__.py"

echo ""
echo "⚙️ Application Layer (app/application/)"
check_dir "app/application"
check_dir "app/application/services"
check_dir "app/application/use_cases"
check_file "app/application/__init__.py"
check_file "app/application/services/__init__.py"
check_file "app/application/services/short_code_service.py"
check_file "app/application/services/url_service.py"
check_file "app/application/use_cases/__init__.py"
check_file "app/application/use_cases/url_use_cases.py"

echo ""
echo "🏢 Infrastructure Layer (app/infrastructure/)"
check_dir "app/infrastructure"
check_dir "app/infrastructure/database"
check_dir "app/infrastructure/cache"
check_dir "app/infrastructure/external"
check_file "app/infrastructure/__init__.py"
check_file "app/infrastructure/database/__init__.py"
check_file "app/infrastructure/database/connection.py"
check_file "app/infrastructure/database/models.py"
check_file "app/infrastructure/database/repositories.py"
check_file "app/infrastructure/cache/__init__.py"
check_file "app/infrastructure/cache/redis.py"
check_file "app/infrastructure/external/__init__.py"
check_file "app/infrastructure/external/services.py"

echo ""
echo "🔌 Interfaces Layer (app/interfaces/)"
check_dir "app/interfaces"
check_dir "app/interfaces/api"
check_dir "app/interfaces/schemas"
check_file "app/interfaces/__init__.py"
check_file "app/interfaces/api/__init__.py"
check_file "app/interfaces/api/routes.py"
check_file "app/interfaces/api/dependencies.py"
check_file "app/interfaces/schemas/__init__.py"

echo ""
echo "📦 Database Migrations (migrations/)"
check_dir "migrations"
check_dir "migrations/versions"
check_file "migrations/env.py"
check_file "migrations/alembic.ini"
check_file "migrations/versions/__init__.py"
check_file "migrations/versions/001_create_initial_schema.py"

echo ""
echo "🧪 Tests (tests/)"
check_dir "tests"
check_dir "tests/unit"
check_dir "tests/integration"
check_file "tests/__init__.py"
check_file "tests/unit/__init__.py"
check_file "tests/unit/test_short_code_service.py"
check_file "tests/unit/test_external_services.py"
check_file "tests/unit/test_exceptions.py"
check_file "tests/integration/__init__.py"
check_file "tests/integration/test_api.py"

echo ""
echo "=========================================="
echo "🎯 Project Structure Verification Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Review QUICKSTART.md for setup"
echo "2. Run: docker-compose up -d"
echo "3. Visit: http://localhost:8000/docs"
echo ""

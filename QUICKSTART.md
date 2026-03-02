# Quick Start Guide

## 🚀 5-Minute Setup

### Option 1: Docker Compose (Recommended)

```bash
# 1. Navigate to project
cd "e:/FAANG/PROJECTS/URL SHORTENER"

# 2. Start all services
docker-compose up -d

# 3. Verify services are running
docker-compose ps

# 4. Access API
# Swagger UI: http://localhost:8000/docs
# API: http://localhost:8000/api/v1
```

### Option 2: Local Development

#### Prerequisites
- Python 3.11+
- PostgreSQL 16 running locally
- Redis running locally

```bash
# 1. Create virtual environment
python -m venv venv
source venv/Scripts/activate  # Windows

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set environment variables
cp .env .env.local
# Edit .env.local with your database/redis URLs

# 4. Initialize database
alembic upgrade head

# 5. Start server
uvicorn app.main:app --reload --port 8000
```

## 📚 Usage Examples

### 1. Shorten a URL

```bash
curl -X POST http://localhost:8000/api/v1/shorten \
  -H "Content-Type: application/json" \
  -d '{
    "long_url": "https://www.github.com/python/cpython",
    "custom_alias": "python-repo",
    "expiration_days": 30
  }'

# Response (201 Created)
{
  "short_code": "python-repo",
  "short_url": "http://localhost:8000/python-repo",
  "long_url": "https://www.github.com/python/cpython",
  "expires_at": "2025-03-28T12:00:00",
  "created_at": "2025-02-26T12:00:00"
}
```

### 2. Redirect to Original URL

```bash
# Browser or curl
curl -L http://localhost:8000/python-repo

# Will redirect to the original long URL
# Automatically tracks the click
```

### 3. Get Analytics

```bash
curl http://localhost:8000/api/v1/analytics/python-repo?days=30

# Response
{
  "short_code": "python-repo",
  "total_clicks": 342,
  "unique_visitors": 128,
  "clicks_per_day": {
    "2025-02-26": 45,
    "2025-02-27": 67,
    "2025-02-28": 89
  },
  "top_referrers": [
    ["https://twitter.com", 120],
    ["https://reddit.com", 89]
  ],
  "country_distribution": {
    "US": 150,
    "GB": 45,
    "CA": 25
  ],
  "last_click_at": "2025-02-28T23:59:00"
}
```

## 🧪 Running Tests

```bash
# All tests with coverage
pytest tests -v --cov=app --cov-report=html

# Unit tests only
pytest tests/unit -v

# Integration tests only
pytest tests/integration -v

# Specific test
pytest tests/unit/test_short_code_service.py::TestSnowflakeIDGenerator -v
```

## 📊 API Documentation

### Interactive Docs (Swagger UI)
```
http://localhost:8000/docs
```

### ReDoc
```
http://localhost:8000/redoc
```

### OpenAPI Schema
```
http://localhost:8000/openapi.json
```

## 🔧 Common Commands

### Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "Add new column"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# Show migration history
alembic history
```

### Database Management

```bash
# Connect to database locally
psql -U postgres -d urlshortener

# Common queries
SELECT COUNT(*) FROM urls;
SELECT COUNT(*) FROM click_events;
SELECT * FROM urls WHERE user_id = 1;
```

### Redis Commands

```bash
# Access Redis CLI
redis-cli

# Get cached URL
GET url:abc123

# Get click count
GET clicks:abc123

# Get all keys
KEYS *

# Clear all cache
FLUSHDB
```

## 📈 Performance Benchmarking

```bash
# Using Apache Bench (installed via Docker)
docker exec urlshortener_api \
  ab -n 10000 -c 100 http://localhost:8000/api/v1/health

# Using curl for simple test
for i in {1..100}; do
  curl -s http://localhost:8000/api/v1/health
done
```

## 🐛 Troubleshooting

### Connection Refused
```bash
# Check if services are running
docker-compose ps

# View logs
docker-compose logs -f api
docker-compose logs -f db
docker-compose logs -f redis
```

### Database Errors
```bash
# Reset database
docker-compose down -v
docker-compose up -d

# Verify connection
docker exec urlshortener_db pg_isready
```

### Memory Issues
```bash
# Increase Docker memory limits
# Edit docker-compose.yml:
services:
  api:
    deploy:
      resources:
        limits:
          memory: 4G
```

## 📖 Architecture Overview

```
┌──────────────┐
│ HTTP Request │
└───────┬──────┘
        ↓
┌──────────────────────────────┐
│  FastAPI Application Layer   │
├──────────────────────────────┤
│  Application Services        │
│  (Business Logic)            │
├──────────────────────────────┤
│  Infrastructure Layer        │
│  (Repos, Cache, External)    │
├──────────────────────────────┤
│  PostgreSQL  │  Redis        │
└──────────────┴───────────────┘
```

## 🎯 Next Steps

1. **Explore the API:**
   - Visit http://localhost:8000/docs
   - Create test short URLs
   - View analytics

2. **Understand the Code:**
   - Read the domain layer (pure business logic)
   - Study the application services
   - Review the database repositories

3. **Run Tests:**
   - Unit tests: `pytest tests/unit`
   - Integration tests: `pytest tests/integration`

4. **Deploy:**
   - Build Docker image: `docker build -t url-shortener:v1 .`
   - Push to registry: `docker push your-registry/url-shortener:v1`
   - Deploy to K8s/ECS/etc.

## 📞 Common Issues & Solutions

| Issue | Cause | Solution |
|-------|-------|----------|
| Port already in use | Another service on 8000 | `lsof -i :8000` or change port |
| Database connection error | PostgreSQL not running | `docker-compose up db` |
| Redis timeout | Redis not accessible | `docker exec redis redis-cli ping` |
| Slow requests | Cold start/cache miss | Make multiple requests or use warmup |
| 404 on redirect | Short code not found | Verify short code in database |

## 📚 Further Reading

- **README.md** - Project overview and features
- **ARCHITECTURE.md** - Detailed architecture and scaling strategy
- **SYSTEM_DESIGN.md** - System design decisions and analysis
- **Code Comments** - Inline documentation throughout codebase

---

**Pro Tips:**
1. Use Swagger UI to test endpoints visually
2. Enable DEBUG mode locally for faster feedback
3. Check Redis memory usage regularly
4. Set up monitoring/alerting for production
5. Use environment variables for all secrets

**Questions?** Check the docs or review the code comments!

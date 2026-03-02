# URL Shortening + Analytics API

A production-grade, scalable URL shortening and analytics service built with FastAPI, PostgreSQL, and Redis. Designed as a system design interview-ready solution.

## 🏗️ Architecture Overview

### Clean Architecture Layers

```
app/
├── domain/               # Core business logic (no dependencies)
│   ├── entities/        # Domain models (User, ShortenedURL, ClickEvent)
│   └── repositories/    # Repository interfaces (contracts)
│
├── application/         # Application logic & use cases
│   ├── services/        # Business services
│   └── use_cases/       # Use case orchestration
│
├── infrastructure/      # External services & frameworks
│   ├── database/        # SQLAlchemy ORM models & repositories
│   ├── cache/           # Redis client & operations
│   └── external/        # GeoIP, URL validation, etc.
│
├── interfaces/          # API & external contracts
│   ├── api/             # FastAPI routes & dependency injection
│   └── schemas/         # Pydantic request/response models
│
└── core/                # Cross-cutting concerns
    ├── config.py        # Environment configuration
    ├── security.py      # JWT, password hashing
    ├── logging.py       # Structured logging
    └── exceptions.py    # Custom exceptions
```

## 🚀 Core Features

### 1. URL Shortening
- **Endpoint:** `POST /api/v1/shorten`
- **Features:**
  - URL validation and normalization
  - Idempotency support (same URL returns same short code)
  - Custom alias option
  - Optional expiration dates
  - Unique code generation (Snowflake algorithm)
  - Collision detection

### 2. Redirection
- **Endpoint:** `GET /{short_code}`
- **Strategy:**
  - Redis cache for O(1) lookups (cache hit rate: ~85-95%)
  - Database fallback on cache miss
  - Automatic cache population
  - Async click event tracking
  - Graceful handling of expired/invalid links

### 3. Analytics
- **Endpoint:** `GET /api/v1/analytics/{short_code}`
- **Metrics:**
  - Total clicks
  - Unique visitors (HyperLogLog)
  - Clicks per day
  - Top referrers
  - Country distribution (GeoIP)
  - Last click timestamp

### 4. Rate Limiting
- Redis-based sliding window rate limiter
- Configurable by IP address
- Protects `POST /shorten` endpoint
- Default: 100 requests/60s

## 🛠️ Tech Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| Language | Python | 3.11+ |
| Framework | FastAPI | 0.109.0 |
| Async ORM | SQLAlchemy | 2.0.23 |
| Database | PostgreSQL | 16 |
| Cache | Redis | 7 |
| Validation | Pydantic | 2.5.2 |
| Authentication | JWT (python-jose) | 3.3.0 |
| Testing | Pytest | 7.4.3 |
| Container | Docker | Latest |

## 📊 Database Schema

### Users Table
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    INDEX idx_users_email (email),
    INDEX idx_users_username (username)
);
```

### URLs Table
```sql
CREATE TABLE urls (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id) ON DELETE CASCADE,
    short_code VARCHAR(12) UNIQUE NOT NULL,
    long_url TEXT NOT NULL,
    expires_at DATETIME,
    is_active BOOLEAN DEFAULT true,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    INDEX idx_urls_short_code (short_code),
    INDEX idx_urls_user_id (user_id),
    INDEX idx_urls_created_at (created_at),
    INDEX idx_urls_expires_at (expires_at)
);
```

### Click Events Table (Append-Only)
```sql
CREATE TABLE click_events (
    id SERIAL PRIMARY KEY,
    shortened_url_id INT NOT NULL REFERENCES urls(id) ON DELETE CASCADE,
    ip_address VARCHAR(45) NOT NULL,
    user_agent VARCHAR(500),
    referrer VARCHAR(500),
    country VARCHAR(2),
    timestamp DATETIME NOT NULL,
    INDEX idx_click_events_shortened_url_id (shortened_url_id),
    INDEX idx_click_events_timestamp (timestamp),
    INDEX idx_click_events_ip_address (ip_address),
    INDEX idx_click_events_url_timestamp (shortened_url_id, timestamp),
    INDEX idx_click_events_url_ts_country (shortened_url_id, timestamp, country)
);
```

## 🚄 Performance Optimizations

### Caching Strategy
```
Request
  ↓
Redis Cache (check)
  ├─ HIT (85-95% of requests)
  │   └─ Return immediately (O(1), ~1-2ms)
  │
  └─ MISS
      ├─ PostgreSQL (fetch)
      ├─ Populate Redis (TTL: 24h)
      └─ Return (~10-50ms)
```

### Click Tracking
```
Redirect Request
  ↓
Async Click Processing
  ├─ Increment Redis counters (real-time)
  ├─ Track unique visitor (HyperLogLog)
  ├─ Track referrer (Sorted Set)
  └─ Store event in DB (background)
```

### Analytics Aggregation
- **Real-time:** Redis counters, HyperLogLog, Sorted Sets
- **Historical:** PostgreSQL with indexed queries
- **Hybrid approach:** Redis for 1-hour window, DB for historical

## 📈 Scalability Architecture

### Horizontal Scaling

```
Load Balancer
    ↓
    ├─ App Instance 1 ─┐
    ├─ App Instance 2 ──┤→ PostgreSQL (Primary)
    ├─ App Instance 3 ──┤→ Redis Cluster
    └─ App Instance N ─┘
```

### Database Sharding Strategy

**Shard Key:** `short_code` hash

```
short_code hash % N_shards → Shard ID

Example (4 shards):
- Shard 0: short codes 0-24
- Shard 1: short codes 25-49
- Shard 2: short codes 50-74
- Shard 3: short codes 75-99
```

### Click Events Partitioning

**By Time:** Partition by DATE(timestamp)

```sql
-- Monthly partitions for hot data
CREATE TABLE click_events_2025_02 PARTITION OF click_events
    FOR VALUES FROM ('2025-02-01') TO ('2025-03-01');

CREATE TABLE click_events_2025_01 PARTITION OF click_events
    FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');

-- Archive old partitions to cold storage
```

### Caching Layers

| Layer | Technology | Strategy | TTL |
|-------|-----------|----------|-----|
| Edge | CDN | URL mappings | 1h |
| App | Redis | URL cache | 24h |
| DB | PostgreSQL | Persistent store | ∞ |

### Read Replica Strategy

```
Writes → PostgreSQL Primary
Reads:
  ├─ Real-time clicks → Redis
  ├─ Analytics queries → PostgreSQL Read Replica
  └─ Historical queries → Archive DB
```

## 🔍 Key Design Decisions

### 1. Snowflake ID Generation
- **Why:** Guaranteed unique IDs without DB coordination
- **Benefit:** Twitter-style scalability
- **Structure:**
  - 41 bits: Timestamp
  - 10 bits: Machine/Datacenter ID
  - 12 bits: Sequence
  - Supports billions of IDs per second

### 2. Async Everywhere
- **Benefits:** High concurrency, non-blocking I/O
- **Implementation:** AsyncIO + asyncpg + async Redis

### 3. Repository Pattern
- **Clean separation** between domain and infrastructure
- **Easy testing** with mock repositories
- **Flexible persistence** layer swapping

### 4. Append-Only Click Events
- **Immutability:** No updates, only inserts
- **Performance:** Faster writes, natural partitioning
- **Analytics:** Audit trail and historical analysis

### 5. Distributed Counters
- **Real-time analytics** via Redis
- **Scalable:** No single point of contention
- **Fallback:** Database for durability

## 🚀 Getting Started

### Prerequisites
- Docker & Docker Compose
- Python 3.11+ (for local development)
- PostgreSQL 16
- Redis 7

### Installation

**1. Clone and setup:**
```bash
cd "e:/FAANG/PROJECTS/URL SHORTENER"

# Create virtual environment
python -m venv venv
source venv/Scripts/activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

**2. Configure environment:**
```bash
cp .env.example .env
# Edit .env with your settings
```

**3. Start services with Docker Compose:**
```bash
docker-compose up -d
```

**4. Run migrations:**
```bash
alembic upgrade head
```

**5. Start API:**
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### API Documentation
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

## 📝 API Examples

### Shorten URL
```bash
curl -X POST http://localhost:8000/api/v1/shorten \
  -H "Content-Type: application/json" \
  -d '{
    "long_url": "https://www.example.com/very/long/path",
    "expiration_days": 30
  }'

# Response
{
  "short_code": "abc123",
  "short_url": "http://localhost:8000/abc123",
  "long_url": "https://www.example.com/very/long/path",
  "expires_at": "2025-03-28T12:00:00",
  "created_at": "2025-02-26T12:00:00"
}
```

### Redirect
```bash
curl -L http://localhost:8000/abc123
# Redirects to: https://www.example.com/very/long/path
```

### Get Analytics
```bash
curl http://localhost:8000/api/v1/analytics/abc123?days=30

# Response
{
  "short_code": "abc123",
  "total_clicks": 1542,
  "unique_visitors": 892,
  "clicks_per_day": {
    "2025-02-26": 250,
    "2025-02-27": 310
  },
  "top_referrers": [
    ["https://twitter.com", 450],
    ["https://reddit.com", 320]
  ],
  "country_distribution": {
    "US": 600,
    "GB": 200,
    "CA": 150
  },
  "last_click_at": "2025-02-27T23:59:00"
}
```

## 🧪 Testing

### Run unit tests:
```bash
pytest tests/unit -v --cov=app
```

### Run integration tests:
```bash
pytest tests/integration -v
```

### Run all tests with coverage:
```bash
pytest tests -v --cov=app --cov-report=html
```

## 📊 Performance Metrics

### Expected Performance

| Operation | P50 | P95 | P99 |
|-----------|-----|-----|-----|
| POST /shorten | 45ms | 120ms | 250ms |
| GET /{code} (cache hit) | 2ms | 5ms | 10ms |
| GET /{code} (cache miss) | 35ms | 80ms | 150ms |
| GET /analytics | 100ms | 300ms | 500ms |

### Throughput

- **Shorten URLs:** 1,000-2,000 req/s per instance
- **Redirects:** 5,000-10,000 req/s per instance
- **Analytics:** 500-1,000 req/s per instance

### Scalability

- **100K URLs:** Single instance, ~500MB memory
- **1M URLs:** 2-3 instances, PostgreSQL primary + 2 read replicas
- **10M URLs:** Database sharding (4-8 shards) + Redis cluster
- **100M URLs:** Full microservices + event streaming (Kafka)

## 🔐 Security Features

### Implemented
- URL validation (prevent open redirects)
- Rate limiting (prevent abuse)
- Bcrypt password hashing
- JWT token authentication (optional)
- CORS configuration
- SQL injection prevention (parameterized queries)

### Production Checklist
- [ ] Enable HTTPS everywhere
- [ ] Rotate JWT secret regularly
- [ ] Enable database backups
- [ ] Set up Redis persistence
- [ ] Monitor for anomalies
- [ ] Enable audit logging
- [ ] Use environment variables for secrets
- [ ] Enable database encryption at rest

## 🛠️ Database Migrations

### Create new migration:
```bash
alembic revision --autogenerate -m "Add new column"
```

### Apply migrations:
```bash
alembic upgrade head
```

### Rollback:
```bash
alembic downgrade -1
```

## 📚 Project Structure

```
.
├── app/                          # Main application
│   ├── domain/                  # Business logic (entities, repositories)
│   ├── application/             # Services & use cases
│   ├── infrastructure/          # Database, cache, external services
│   ├── interfaces/              # API routes & schemas
│   ├── core/                    # Config, security, logging
│   └── main.py                  # FastAPI app entry point
├── migrations/                   # Alembic schema migrations
├── tests/                        # Unit & integration tests
├── Dockerfile                    # Container image
├── docker-compose.yml           # Local environment
├── requirements.txt             # Python dependencies
├── .env                         # Environment configuration
└── README.md                    # This file
```

## 🎯 Future Enhancements

### Phase 2: User Management
- [ ] User registration & authentication
- [ ] Personal dashboard
- [ ] Link ownership & access control
- [ ] Usage quotas

### Phase 3: Analytics & Insights
- [ ] Real-time analytics dashboard
- [ ] Advanced filtering & segmentation
- [ ] Export reports (CSV/PDF)
- [ ] Webhooks for click events

### Phase 4: Enterprise Features
- [ ] Custom domains
- [ ] Link password protection
- [ ] QR code generation
- [ ] A/B testing support
- [ ] API keys & rate limit tiers

### Phase 5: Microservices
- [ ] Separate analytics service
- [ ] Event streaming (Kafka)
- [ ] GraphQL API
- [ ] Mobile apps

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see LICENSE file for details.

## 🙏 Acknowledgments

- FastAPI documentation and examples
- System Design Interview resources
- Clean Architecture principles by Robert C. Martin

# Architecture & Scaling Strategy

## System Design Overview

This document explains the architectural decisions and scaling strategies for production deployment.

## 1. Clean Architecture Implementation

### Layer Separation

```
┌─────────────────────────────────────────────────────────┐
│                    FastAPI (Web)                         │
│              ↓ HTTP Requests/Responses                   │
├─────────────────────────────────────────────────────────┤
│         Interfaces Layer (API Routes, Schemas)           │
│              ↓                                           │
│  ┌─────────────────────────────────────────────────┐    │
│  │     Application Layer (Services, Use Cases)     │    │
│  │    • URLShorteningService                       │    │
│  │    • AnalyticsService                           │    │
│  │    • ShortenURLUseCase                          │    │
│  │    • ResolveURLUseCase                          │    │
│  └─────────────────────────────────────────────────┘    │
│              ↓                                           │
│  ┌─────────────────────────────────────────────────┐    │
│  │    Domain Layer (Pure Business Logic)           │    │
│  │    • User, ShortenedURL entities                │    │
│  │    • Repository interfaces                      │    │
│  │    • No external dependencies                   │    │
│  └─────────────────────────────────────────────────┘    │
│              ↓                                           │
│  ┌─────────────────────────────────────────────────┐    │
│  │  Infrastructure Layer (Implementation)          │    │
│  │    • SQLAlchemy repositories                    │    │
│  │    • Redis cache service                        │    │
│  │    • External API clients                       │    │
│  └─────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
       ↓                 ↓                 ↓
   PostgreSQL         Redis           GeoIP API
```

### Benefits

1. **Testability:** Each layer can be tested independently with mocks
2. **Maintainability:** Clear separation of concerns
3. **Flexibility:** Easy to swap implementations (e.g., Redis → Memcached)
4. **Scalability:** Services are stateless and horizontally scalable

## 2. Scalability Architecture

### 2.1 Horizontal Scaling

```
                    ┌─────────────────┐
                    │  Load Balancer  │
                    │   (e.g., nginx) │
                    └────────┬────────┘
                 ┌──────────┼──────────┐
                 ↓          ↓          ↓
            ┌────────┐ ┌────────┐ ┌────────┐
            │ App #1 │ │ App #2 │ │ App #3 │
            └────┬───┘ └────┬───┘ └────┬───┘
                 │          │          │
                 └──────────┼──────────┘
                            ↓
                    ┌──────────────────┐
                    │  PostgreSQL DB   │
                    │    (Primary)     │
                    └──────────────────┘
                            ↓
                    ┌──────────────────┐
                    │  Read Replicas   │
                    │  (Standby 1, 2)  │
                    └──────────────────┘
```

**Deployment:** Docker Swarm or Kubernetes

```yaml
services:
  api:
    replicas: 5
    placement:
      constraints:
        - node.role == worker
    resources:
      limits:
        cpus: '2'
        memory: 2G
      reservations:
        cpus: '1'
        memory: 1G
```

### 2.2 Database Scaling

#### Read Replicas

```
Write
  ↓
Primary DB (PostgreSQL)
  ├─ Replication
  ├─ Read Replica #1
  └─ Read Replica #2
```

**Routing:**
```python
# Writes → Primary
session = primary_db.connect()

# Reads (analytics) → Read Replica
analytics_db = read_replica_db.connect()
```

#### Database Sharding

**When to shard:** 100M+ URLs

**Shard Strategy:**
```
short_code_hash % num_shards → shard_id

Example (8 shards, 3 replicas each):
Shard 0: short_code % 8 == 0 (Master + 2 Replicas)
Shard 1: short_code % 8 == 1 (Master + 2 Replicas)
...
Shard 7: short_code % 8 == 7 (Master + 2 Replicas)
```

**Shard-Aware Repository:**
```python
class ShardedURLRepository:
    async def get_by_short_code(self, short_code: str):
        shard_id = hash(short_code) % self.num_shards
        session = self.shard_sessions[shard_id]
        return await session.execute(...)
```

#### Click Events Partitioning

**Time-based partitioning:**
```sql
-- Create partitioned table
CREATE TABLE click_events (
    id SERIAL,
    shortened_url_id INT,
    ip_address VARCHAR(45),
    timestamp DATETIME,
    ...
) PARTITION BY RANGE (YEAR(timestamp), MONTH(timestamp));

-- Create monthly partitions
CREATE TABLE click_events_202502 PARTITION OF click_events
    FOR VALUES FROM (2025, 2) TO (2025, 3);

CREATE TABLE click_events_202503 PARTITION OF click_events
    FOR VALUES FROM (2025, 3) TO (2025, 4);
```

**Benefits:**
- Faster queries on recent data (hot partition)
- Archive old partitions to cold storage
- Easier VACUUM and maintenance

### 2.3 Caching Architecture

```
┌────────────────┐                 ┌─────────────────┐
│  User Request  │────────────────→│  Load Balancer  │
└────────────────┘                 └────────┬────────┘
                                            ↓
                                     ┌──────────────┐
                                     │  App Server  │
                                     └──────┬───────┘
                                            ↓
                                    ┌───────────────────┐
                                    │  Check Cache      │
                                    │  (Redis)          │
                                    └───────┬───────────┘
                               HIT /        \ MISS
                                  /          \
                                 ↓            ↓
                            Return        Query DB
                            to User       (PostgreSQL)
                                            ↓
                                    Populate Cache
                                    (TTL: 24 hours)
                                            ↓
                                    Return to User
```

**Cache Key Strategies:**

```python
# URL mapping cache
cache_key = f"url:{short_code}"
value = normalized_long_url

# Analytics aggregation
cache_key = f"clicks:{short_code}"
value = click_count

# Unique visitors (HyperLogLog)
cache_key = f"unique_visitors:{short_code}"
value = HyperLogLog

# Top referrers (Sorted Set)
cache_key = f"referrers:{short_code}"
value = {referrer: score, ...}
```

**Cache Invalidation:**
```python
# TTL-based (most common)
cache.set(key, value, ttl=86400)  # 24 hours

# Event-based
async def delete_expired_urls():
    expired_urls = get_expired_urls()
    for url in expired_urls:
        cache.delete(f"url:{url.short_code}")
```

### 2.4 Redis Cluster for Large Scale

```
         ┌─────────────────────────────────┐
         │    Redis Cluster (6 nodes)      │
         │  3 masters + 3 replicas         │
         └──────────┬──────────────────────┘
                    │
      ┌─────────────┼─────────────┐
      ↓             ↓             ↓
  Master 1      Master 2      Master 3
  (Keys 0-5K)   (Keys 5K-10K) (Keys 10K-16K)
    ↓             ↓             ↓
  Replica 1    Replica 2    Replica 3
```

**Configuration:**
```python
from redis.cluster import RedisCluster

redis_cluster = RedisCluster(
    startup_nodes=[
        {"host": "redis-1", "port": 6379},
        {"host": "redis-2", "port": 6379},
        {"host": "redis-3", "port": 6379},
    ],
    skip_full_coverage_check=True
)
```

## 3. Request Flow & Data Flow

### Shorten URL Flow

```
POST /api/v1/shorten
{
  "long_url": "https://example.com/very/long/path",
  "expiration_days": 30
}
    ↓
┌─────────────────────────────┐
│  FastAPI Route Handler      │
│  (interfaces/api/routes.py) │
└────────────┬────────────────┘
             ↓
┌─────────────────────────────┐
│  Rate Limiter Check         │
│  (Redis sliding window)     │
│  200/60s per IP             │
└────────────┬────────────────┘
             ↓
┌─────────────────────────────┐
│  ShortenURLUseCase          │
│  (application/use_cases/)   │
└────────────┬────────────────┘
             ↓
┌─────────────────────────────┐
│  URLShorteningService       │
│  - Validate URL             │
│  - Check for idempotency    │
│  - Generate short code      │
└────────────┬────────────────┘
             ↓
┌─────────────────────────────┐
│  ShortenedURLRepository     │
│  - Create in DB             │
│  - Generate unique code     │
└────────────┬────────────────┘
             ↓
┌─────────────────────────────┐
│  Cache Service              │
│  - Store mapping in Redis   │
│  - TTL: 24 hours            │
└────────────┬────────────────┘
             ↓
Response (201 Created)
{
  "short_code": "a1b2c3",
  "short_url": "http://localhost:8000/a1b2c3",
  "long_url": "https://example.com/very/long/path",
  "expires_at": "2025-03-28T12:00:00"
}
```

### Redirect & Click Tracking Flow

```
GET /{short_code}
    ↓
┌─────────────────────────────┐
│  FastAPI Route Handler      │
└────────────┬────────────────┘
             ↓
┌─────────────────────────────┐
│  ResolveURLUseCase          │
│  - Check cache (Redis)      │
└────────────┬────────────────┘
       HIT / \ MISS
        /      \
       ↓        ↓ Query DB
   Cache Hit   DB Query
       │          │
       └─────┬────┘
             ↓
┌─────────────────────────────┐
│  AnalyticsService           │
│  - Async click tracking     │
│  - Update Redis counters    │
└────────────┬────────────────┘
             ↓
┌─────────────────────────────┐
│  Distributed Counter        │
│  - Increment: clicks:{code} │
│  - HyperLogLog: unique IPs  │
│  - ZSet: referrers          │
└────────────┬────────────────┘
             ↓
┌─────────────────────────────┐
│  Background Job             │
│  (Optional: Store event in  │
│   click_events table)       │
└─────────────────────────────┘
             ↓
Response (307 Temporary Redirect)
Location: https://example.com/very/long/path
```

## 4. Failure Handling & Resilience

### Circuit Breaker Pattern

```python
from pybreaker import CircuitBreaker

redis_breaker = CircuitBreaker(
    fail_max=5,           # Trip after 5 failures
    reset_timeout=60,     # Try again after 60s
    exclude=[ConnectionRefused]
)

@redis_breaker
async def get_from_cache(key):
    return await redis.get(key)
```

### Fallback Strategy

```python
async def resolve_url(short_code: str):
    try:
        # Try cache first
        long_url = await cache.get(f"url:{short_code}")
        if long_url:
            return long_url
    except RedisUnavailable:
        logger.warning("Cache unavailable, falling back to DB")
    
    # Query database
    url = await url_repository.get_by_short_code(short_code)
    if not url:
        raise URLNotFoundError(short_code)
    
    return url.long_url
```

### Graceful Degradation

```
Scenario: Database is slow
├─ Response time increases
├─ But service remains operational
├─ Cache hits still fast
└─ Users see slightly slower experience

Scenario: Redis is down
├─ All requests hit database
├─ Performance degrades
├─ But service remains operational
└─ Circuit breaker prevents cascading failures
```

## 5. Monitoring & Observability

### Key Metrics

```python
# Response time percentiles
p50_shorten_url: 45ms
p95_shorten_url: 120ms
p99_shorten_url: 250ms

p50_redirect: 2ms (cache hit)
p95_redirect: 40ms (DB hit)

# Throughput
requests_per_second: 1000-5000
cache_hit_rate: 85-95%

# Resource usage
cpu_utilization: 40-60%
memory_utilization: 50-70%
database_connections: 15-20
redis_memory: 100-500MB
```

### Logging Strategy

```
Regular request → INFO
Cache hit       → DEBUG
DB query        → DEBUG
Error/Exception → ERROR
Rate limit      → WARNING
```

### Structured Logging

```json
{
  "timestamp": "2025-02-26T12:00:00Z",
  "level": "ERROR",
  "logger": "urlshortener",
  "message": "Database connection failed",
  "error_code": "DB_CONNECTION_ERROR",
  "user_id": null,
  "request_id": "req-123456",
  "trace_id": "trace-789",
  "span_id": "span-456"
}
```

## 6. Migration Path to Microservices

### Current Monolith

```
Single FastAPI Application
├─ URL Shortening Logic
├─ Analytics Logic
├─ User Management (future)
└─ Single PostgreSQL Database
```

### Future Microservices

```
┌────────────────────────────────────┐
│        API Gateway                  │
│      (Route, Rate Limit)            │
└────────────────┬───────────────────┘
       │         │         │
   ┌───↓──┐  ┌──↓───┐  ┌───↓──┐
   │Shorten│  │Analytics│User  │
   │Service│  │Service  │Service│
   └────┬──┘  └────┬───┘  └───┬──┘
        │         │          │
   ┌────↓────┬────↓────┬────↓────┐
   │PostgreSQL│PostgreSQL│PostgreSQL│
   │ (Shorten)│(Analytics)│(Users)   │
   └─────────┴──────────┴───────────┘
        │
        └─────────────┐
                      ↓
              Event Stream (Kafka)
              - Click Events
              - URL Created
              - Errors
```

### Service Separation Strategy

1. **Phase 1:** Analytics as separate service
   - Consumes from message queue
   - Independent database
   - Enables scaling analytics independently

2. **Phase 2:** User Management service
   - Authentication & authorization
   - User profiles & settings
   - Billing & quotas

3. **Phase 3:** Event processing
   - Real-time analytics
   - Recommendations
   - Anomaly detection

## 7. Disaster Recovery & Backup

### Backup Strategy

```
PostgreSQL:
├─ Continuous WAL archiving
├─ Daily full backups
├─ Weekly incremental backups
└─ 30-day retention

Redis:
├─ RDB snapshots every 6 hours
├─ AOF (Append-Only File)
└─ Replicated across 3 nodes
```

### Recovery Procedure

```
Data Loss Scenario:
1. Alert triggered (automated)
2. Database restored from backup
3. Redis cluster rebuilt from backup
4. Analytics re-aggregated from events
5. Service checks (healthcheck)
6. Gradual traffic restoration
```

## 8. Cost Optimization

### Resource Allocation

```
Development:
- 2 GB memory per instance
- 2 CPU cores per instance
- Single database (t3.small)

Production (Baseline):
- 4+ GB memory per instance
- 4+ CPU cores per instance
- PostgreSQL: db.r5.xlarge (32GB, 4vCPU)
- Redis: r5.large (16GB)
- 3-5 app instances

Production (Scale):
- 8+ GB memory per instance
- 8+ CPU cores per instance
- PostgreSQL read replicas
- Redis cluster
- 10+ app instances
```

### Cost Breakdown (Monthly)

```
Infrastructure:
├─ Compute (5 × t3.medium):      ~$150
├─ Database (db.r5.xlarge):       ~$500
├─ Redis (r5.large):              ~$200
├─ Storage (EBS):                 ~$100
└─ Network/Bandwidth:             ~$50
                        Total: ~$1000/month

Scaling (Add more capacity):
├─ Scale to 100K URLs:   Minimal cost increase
├─ Scale to 1M URLs:     ~$150 increase (replicas)
├─ Scale to 10M URLs:    ~$500 increase (sharding)
└─ Scale to 100M+ URLs:  Microservices + Kafka
```

## 9. Performance Testing

### Load Testing Scenario

```bash
# Using Apache Bench or Locust
ab -n 100000 -c 500 http://localhost:8000/api/v1/health

# Locust scenario
Users: 1000
Spawn rate: 50 users/sec
Duration: 1 hour

Expected results:
├─ 95th percentile: < 200ms
├─ 99th percentile: < 500ms
├─ Error rate: < 0.1%
└─ Throughput: 2000+ req/s
```

---

**Document Version:** 1.0  
**Last Updated:** 2025-02-26  
**Maintainer:** Architecture Team

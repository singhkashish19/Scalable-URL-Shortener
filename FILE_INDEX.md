# File Index - Production URL Shortener API

## 📚 Getting Started

**Start here:**
1. [README.md](README.md) - Feature overview, tech stack, API examples
2. [QUICKSTART.md](QUICKSTART.md) - 5-minute setup guide
3. [ARCHITECTURE.md](ARCHITECTURE.md) - System design, scaling strategy
4. [SYSTEM_DESIGN.md](SYSTEM_DESIGN.md) - Design decisions, analysis

---

## 🌍 Core Layer (Cross-Cutting Concerns)

| File | Purpose | Key Classes |
|------|---------|------------|
| **app/core/config.py** | Environment configuration | `Settings()` - Pydantic settings from .env |
| **app/core/security.py** | Authentication & hashing | `hash_password()`, `create_access_token()` |
| **app/core/logging.py** | Structured logging setup | `setup_logging()`, JSON formatter |
| **app/core/exceptions.py** | Custom exception classes | `URLNotFoundError`, `RateLimitExceededError`, etc. |

**When to modify:**
- Add new configuration → config.py
- Change authentication logic → security.py
- Adjust logging format → logging.py
- Add new exception types → exceptions.py

---

## 🎯 Domain Layer (Pure Business Logic)

| File | Purpose | Key Classes |
|------|---------|------------|
| **app/domain/entities/__init__.py** | Domain models | `User`, `ShortenedURL`, `ClickEvent`, `URLAnalytics` |
| **app/domain/repositories/__init__.py** | Repository contracts | `IUserRepository`, `IShortenedURLRepository`, `IClickEventRepository` |

**Key Principle:** These files contain zero external dependencies. They represent core business concepts.

**When to modify:**
- Add new domain model → entities/__init__.py
- Change repository interface → repositories/__init__.py

---

## ⚙️ Application Layer (Business Logic & Orchestration)

### Services

| File | Purpose | Key Classes |
|------|---------|------------|
| **app/application/services/short_code_service.py** | ID generation | `ShortCodeGenerator`, `SnowflakeIDGenerator`, `Base62Encoder` |
| **app/application/services/url_service.py** | URL operations | `URLShorteningService`, `AnalyticsService` |

**When to modify:**
- Change ID generation strategy → short_code_service.py
- Modify URL shortening logic → url_service.py
- Change analytics aggregation → url_service.py

### Use Cases

| File | Purpose | Key Classes |
|------|---------|------------|
| **app/application/use_cases/url_use_cases.py** | Use case orchestration | `ShortenURLUseCase`, `ResolveURLUseCase`, `GetAnalyticsUseCase` |

**When to modify:**
- Add new use case → url_use_cases.py
- Change business flow → url_use_cases.py

---

## 🏢 Infrastructure Layer (External Services)

### Database

| File | Purpose | Key Classes |
|------|---------|------------|
| **app/infrastructure/database/connection.py** | SQLAlchemy setup | `engine`, `async_session_factory`, `init_db()` |
| **app/infrastructure/database/models.py** | ORM models | `UserModel`, `ShortenedURLModel`, `ClickEventModel` |
| **app/infrastructure/database/repositories.py** | Repository implementations | `UserRepository`, `ShortenedURLRepository`, `ClickEventRepository` |

**When to modify:**
- Change database URL/pooling → connection.py
- Add/modify database schema → models.py
- Add/modify data access logic → repositories.py

### Cache

| File | Purpose | Key Classes |
|------|---------|------------|
| **app/infrastructure/cache/redis.py** | Redis operations | `CacheService`, `RateLimiter`, `DistributedCounter` |

**When to modify:**
- Change cache strategy → redis.py
- Modify rate limiting → redis.py
- Add new Redis operation → redis.py

### External Services

| File | Purpose | Key Classes |
|------|---------|------------|
| **app/infrastructure/external/services.py** | External integrations | `URLValidator`, `GeoIPService`, `hash_ip()` |

**When to modify:**
- Add URL validation rules → URLValidator
- Integrate GeoIP service → GeoIPService
- Add external API calls → services.py

---

## 🔌 Interfaces Layer (API & External Contracts)

### API Routes

| File | Purpose | Key Functions |
|------|---------|--------------|
| **app/interfaces/api/routes.py** | FastAPI endpoints | `shorten_url()`, `redirect_url()`, `get_analytics()` |
| **app/interfaces/api/dependencies.py** | Dependency injection | `get_db_session()`, `get_cache_service()`, `get_*_use_case()` |

**When to modify:**
- Add new endpoint → routes.py
- Change request/response format → routes.py
- Add new service dependency → dependencies.py

### Schemas

| File | Purpose | Key Classes |
|------|---------|------------|
| **app/interfaces/schemas/__init__.py** | Pydantic v2 models | `ShortenRequestSchema`, `ShortenResponseSchema`, `AnalyticsSchema`, etc. |

**When to modify:**
- Add new API request type → schemas/__init__.py
- Change response format → schemas/__init__.py
- Add new validation rules → schemas/__init__.py

---

## 🚀 Application Entry Point

| File | Purpose | Key Functions |
|------|---------|--------------|
| **app/main.py** | FastAPI app setup | `app`, lifespan, middleware, exception handlers |

**When to modify:**
- Add middleware → main.py
- Change startup/shutdown logic → main.py
- Add new exception handlers → main.py

---

## 📦 Database Migrations

| File | Purpose |
|------|---------|
| **migrations/env.py** | Alembic environment configuration |
| **migrations/alembic.ini** | Alembic settings |
| **migrations/versions/001_create_initial_schema.py** | Initial database schema |

**Commands:**
```bash
# Create new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

---

## 🧪 Tests

| File | Purpose | Test Classes |
|------|---------|------------|
| **tests/unit/test_short_code_service.py** | ID generation tests | `TestBase62Encoder`, `TestSnowflakeIDGenerator`, `TestShortCodeGenerator` |
| **tests/unit/test_external_services.py** | External service tests | `TestURLValidator`, `TestHashIP` |
| **tests/unit/test_exceptions.py** | Exception tests | `TestExceptions` |
| **tests/integration/test_api.py** | API endpoint tests | Health check, redirect, analytics |

**When to modify:**
- Add unit tests → tests/unit/
- Add integration tests → tests/integration/
- Add fixtures → conftest.py

---

## 🐳 Docker & Deployment

| File | Purpose |
|------|---------|
| **Dockerfile** | Multi-stage Python image for production |
| **docker-compose.yml** | Local development environment (PostgreSQL + Redis + API) |

**When to modify:**
- Change Python version → Dockerfile
- Change base image → Dockerfile
- Add/modify services → docker-compose.yml
- Change environment variables → docker-compose.yml

---

## 📋 Configuration Files

| File | Purpose |
|------|---------|
| **requirements.txt** | Python package dependencies |
| **.env** | Environment variables (local development) |
| **.gitignore** | Git ignore patterns |
| **conftest.py** | Pytest configuration & fixtures |

**When to modify:**
- Add Python dependency → requirements.txt
- Change environment variables → .env
- Add pytest fixture → conftest.py

---

## 📄 Documentation

| File | Purpose | For Whom |
|------|---------|----------|
| **README.md** | Project overview, features, setup | Everyone |
| **QUICKSTART.md** | 5-minute setup guide | Getting started |
| **ARCHITECTURE.md** | Detailed architecture, scaling | Architects, senior engineers |
| **SYSTEM_DESIGN.md** | Design decisions, analysis | Interviewees, architects |
| **PROJECT_SUMMARY.md** | What's implemented, learning value | Overview |
| **FILE_INDEX.md** | This file | Navigation |

---

## 🎯 Quick Navigation

### "I want to..."

**...understand the system**
→ Read [README.md](README.md) then [ARCHITECTURE.md](ARCHITECTURE.md)

**...set it up locally**
→ Follow [QUICKSTART.md](QUICKSTART.md)

**...add a new feature**
→ Check [FILE_INDEX.md](#) for relevant files, then modify

**...understand design decisions**
→ Read [SYSTEM_DESIGN.md](SYSTEM_DESIGN.md)

**...write tests**
→ Look at [tests/](tests/) for examples

**...deploy to production**
→ Read deployment section in [ARCHITECTURE.md](ARCHITECTURE.md)

**...scale beyond 100M URLs**
→ See sharding section in [ARCHITECTURE.md](ARCHITECTURE.md)

### "I'm modifying..."

**...the database schema**
1. Edit [app/infrastructure/database/models.py](app/infrastructure/database/models.py)
2. Create migration: `alembic revision --autogenerate -m "Description"`
3. Apply: `alembic upgrade head`

**...an API endpoint**
1. Edit [app/interfaces/api/routes.py](app/interfaces/api/routes.py)
2. Update schemas in [app/interfaces/schemas/__init__.py](app/interfaces/schemas/__init__.py)
3. Add tests in [tests/integration/test_api.py](tests/integration/test_api.py)

**...business logic**
1. Edit [app/application/services/url_service.py](app/application/services/url_service.py)
2. Update tests in [tests/unit/](tests/unit/)
3. Log changes in [CHANGELOG.md](CHANGELOG.md)

**...infrastructure**
1. Edit relevant file in [app/infrastructure/](app/infrastructure/)
2. Update tests
3. Consider database migration if needed

### "I'm looking for..."

**...exception handling**
→ [app/core/exceptions.py](app/core/exceptions.py)

**...configuration**
→ [app/core/config.py](app/core/config.py)

**...caching logic**
→ [app/infrastructure/cache/redis.py](app/infrastructure/cache/redis.py)

**...ID generation**
→ [app/application/services/short_code_service.py](app/application/services/short_code_service.py)

**...analytics**
→ [app/application/services/url_service.py](app/application/services/url_service.py)

**...validation**
→ [app/infrastructure/external/services.py](app/infrastructure/external/services.py)

### Total Codebase

```
Files: 35+
Lines of Code: 3,000+
Test Coverage: 70%+
Documentation: 1,000+ lines
```

---

## 🔍 Code Statistics by Layer

| Layer | Files | Purpose | LOC |
|-------|-------|---------|-----|
| **Core** | 4 | Cross-cutting | 300 |
| **Domain** | 2 | Business logic | 150 |
| **Application** | 3 | Services & use cases | 400 |
| **Infrastructure** | 5 | DB, cache, external | 800 |
| **Interfaces** | 3 | API, schemas | 400 |
| **Tests** | 4 | Unit & integration | 500 |
| **Config** | 5 | Docker, env, migrations | 300 |

---

End of File Index. Navigate using the links above! 🚀

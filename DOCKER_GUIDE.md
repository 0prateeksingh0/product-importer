# 🐳 Docker Compose Local Development Guide

## 🎯 Quick Start with Docker

Docker Compose sets up **everything** you need locally:
- PostgreSQL database
- Redis for Celery
- FastAPI web server
- Celery worker

---

## 📦 Prerequisites

1. **Docker Desktop** - Download from https://docker.com
   - For Mac: Download and install Docker Desktop
   - Start Docker Desktop (whale icon in menu bar)

---

## 🚀 Start Everything with One Command

```bash
cd "/Users/tronadoit/Desktop/Product Importer"

# Start all services
docker-compose up

# Or run in background (detached mode)
docker-compose up -d
```

**That's it!** Docker will:
1. Build your application image
2. Start PostgreSQL
3. Start Redis
4. Start FastAPI web server
5. Start Celery worker

**Access your app at:** http://localhost:8000

---

## 📋 Docker Compose Services

Your `docker-compose.yml` defines 4 services:

### 1. **PostgreSQL Database** (`db`)
- Port: 5432
- Database: `product_importer`
- User: `postgres`
- Password: `postgres`

### 2. **Redis** (`redis`)
- Port: 6379
- Used for Celery message broker

### 3. **FastAPI Web** (`web`)
- Port: 8000
- Auto-reloads on code changes
- Access: http://localhost:8000

### 4. **Celery Worker** (`celery_worker`)
- Processes CSV imports in background
- 2 concurrent workers

---

## 🎮 Common Docker Commands

### Start Services
```bash
# Start all services (foreground - see logs)
docker-compose up

# Start in background
docker-compose up -d

# Start specific service
docker-compose up web
```

### Stop Services
```bash
# Stop all services
docker-compose down

# Stop and remove volumes (clean slate)
docker-compose down -v
```

### View Logs
```bash
# All services
docker-compose logs

# Follow logs (real-time)
docker-compose logs -f

# Specific service
docker-compose logs web
docker-compose logs celery_worker

# Last 50 lines
docker-compose logs --tail=50
```

### Check Status
```bash
# List running services
docker-compose ps

# View service details
docker-compose ps web
```

### Restart Services
```bash
# Restart all
docker-compose restart

# Restart specific service
docker-compose restart web
docker-compose restart celery_worker
```

### Rebuild After Code Changes
```bash
# Rebuild images
docker-compose build

# Rebuild and start
docker-compose up --build
```

### Execute Commands in Container
```bash
# Open shell in web container
docker-compose exec web bash

# Run Python commands
docker-compose exec web python
docker-compose exec web python -m app.models

# Check database
docker-compose exec db psql -U postgres -d product_importer

# Redis CLI
docker-compose exec redis redis-cli
```

---

## 📂 Project Structure

```
Product Importer/
├── docker-compose.yml    # Docker services definition
├── Dockerfile           # Application container image
├── requirements.txt     # Python dependencies
├── app/                 # Application code
├── static/              # Frontend files
└── uploads/             # Uploaded CSV files (shared volume)
```

---

## 🔍 Verify Everything is Working

### 1. Check Services are Running
```bash
docker-compose ps
```

Should show all 4 services as "Up":
```
NAME                        STATUS
product_importer_web        Up
product_importer_celery     Up
product_importer_db         Up (healthy)
product_importer_redis      Up (healthy)
```

### 2. Test Web Server
```bash
curl http://localhost:8000/api/health
```

Should return:
```json
{"status":"healthy","timestamp":"..."}
```

### 3. Test Database Connection
```bash
docker-compose exec db psql -U postgres -d product_importer -c "SELECT 1;"
```

Should return:
```
 ?column?
----------
        1
```

### 4. Test Redis
```bash
docker-compose exec redis redis-cli ping
```

Should return:
```
PONG
```

### 5. Open Web UI
Open browser: http://localhost:8000

You should see the Product Importer interface!

---

## 📤 Import CSV with Docker

### Via Web UI
1. Go to http://localhost:8000
2. Click "Import Products" tab
3. Upload your `products.csv`
4. Watch real-time progress!

### Via API
```bash
curl -X POST http://localhost:8000/api/import \
  -F "file=@products.csv"
```

### Check Worker Logs
```bash
docker-compose logs -f celery_worker
```

You'll see the worker processing your CSV in real-time!

---

## 🛠️ Development Workflow

### 1. Make Code Changes
Edit files in your IDE as normal. Changes are **automatically reflected** because of volume mounts!

### 2. View Changes
- **Backend changes** (`.py` files): Auto-reload (watch logs)
- **Frontend changes** (`.html`, `.css`, `.js`): Refresh browser
- **Dependencies** (`requirements.txt`): Need to rebuild

### 3. Add New Dependencies
```bash
# Edit requirements.txt, then:
docker-compose down
docker-compose build
docker-compose up -d
```

### 4. Check Logs During Development
```bash
# In separate terminal, follow logs:
docker-compose logs -f web celery_worker
```

---

## 🗄️ Database Management

### Access Database
```bash
# PostgreSQL shell
docker-compose exec db psql -U postgres -d product_importer
```

### Common SQL Commands
```sql
-- List tables
\dt

-- Count products
SELECT COUNT(*) FROM products;

-- View first 10 products
SELECT * FROM products LIMIT 10;

-- Check import jobs
SELECT * FROM import_jobs ORDER BY started_at DESC;

-- Exit
\q
```

### Backup Database
```bash
docker-compose exec db pg_dump -U postgres product_importer > backup.sql
```

### Restore Database
```bash
docker-compose exec -T db psql -U postgres -d product_importer < backup.sql
```

### Reset Database
```bash
# WARNING: Deletes all data!
docker-compose down -v
docker-compose up -d
```

---

## 🔴 Redis Management

### Access Redis CLI
```bash
docker-compose exec redis redis-cli
```

### Common Redis Commands
```
# Check connection
PING

# View Celery queue length
LLEN celery

# List all keys
KEYS *

# View specific key
GET some_key

# Clear all data (CAREFUL!)
FLUSHALL

# Exit
EXIT
```

---

## 📊 Monitor Celery Worker

### View Worker Status
```bash
# In another terminal
docker-compose logs -f celery_worker
```

### Celery Flower (Optional Monitoring Tool)

Add to `docker-compose.yml`:
```yaml
  flower:
    build: .
    command: celery -A app.celery_app flower --port=5555
    ports:
      - "5555:5555"
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
    depends_on:
      - redis
      - celery_worker
```

Then:
```bash
docker-compose up -d flower
open http://localhost:5555
```

---

## 🐛 Troubleshooting

### Problem: Port 8000 already in use
**Solution:**
```bash
# Kill process using port 8000
lsof -ti:8000 | xargs kill -9

# Or change port in docker-compose.yml:
ports:
  - "8001:8000"  # Access at http://localhost:8001
```

### Problem: Database connection refused
**Solution:**
```bash
# Wait for database to be healthy
docker-compose ps

# Check database logs
docker-compose logs db

# Restart services
docker-compose restart
```

### Problem: Worker not processing jobs
**Solution:**
```bash
# Check worker logs
docker-compose logs celery_worker

# Check Redis connection
docker-compose exec redis redis-cli ping

# Restart worker
docker-compose restart celery_worker
```

### Problem: Changes not reflecting
**Solution:**
```bash
# For Python changes (should auto-reload)
docker-compose restart web

# For dependency changes
docker-compose down
docker-compose build
docker-compose up -d

# For frontend changes (just refresh browser)
```

### Problem: Out of disk space
**Solution:**
```bash
# Remove unused containers and images
docker system prune

# Remove all stopped containers, volumes, networks
docker system prune -a --volumes
```

---

## 🧹 Clean Up

### Remove Containers (Keep Data)
```bash
docker-compose down
```

### Remove Containers and Volumes (Delete Data)
```bash
docker-compose down -v
```

### Remove Images
```bash
docker-compose down --rmi all -v
```

### Complete Cleanup
```bash
# Stop and remove everything
docker-compose down -v --rmi all

# Remove Docker cache
docker system prune -a --volumes
```

---

## 🚀 Production vs Development

### Development (Current Setup)
- ✅ Auto-reload on code changes
- ✅ Debug mode enabled
- ✅ Volume mounts for live editing
- ✅ SQLite (fast, local)

### Production (Render/Heroku)
- ❌ No auto-reload
- ❌ Debug mode disabled
- ❌ No volume mounts
- ✅ PostgreSQL (robust, scalable)

---

## 📝 Docker Compose File Explained

```yaml
version: '3.8'

services:
  # PostgreSQL Database
  db:
    image: postgres:15-alpine      # Lightweight PostgreSQL
    environment:
      POSTGRES_DB: product_importer
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    volumes:
      - postgres_data:/var/lib/postgresql/data  # Persist data
    healthcheck:                   # Wait until ready
      test: ["CMD-SHELL", "pg_isready -U postgres"]

  # Redis
  redis:
    image: redis:7-alpine          # Lightweight Redis
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]

  # FastAPI Web
  web:
    build: .                       # Build from Dockerfile
    command: uvicorn app.main:app --reload  # Auto-reload
    volumes:
      - .:/app                     # Mount code (live editing)
    ports:
      - "8000:8000"                # Expose port
    environment:
      DATABASE_URL: postgresql://postgres:postgres@db:5432/product_importer
      REDIS_URL: redis://redis:6379/0
    depends_on:
      - db                         # Start after db & redis
      - redis

  # Celery Worker
  celery_worker:
    build: .
    command: celery -A app.celery_app worker --loglevel=info
    volumes:
      - .:/app
    environment:
      # Same as web
    depends_on:
      - db
      - redis

volumes:
  postgres_data:                   # Named volume for persistence
```

---

## ✅ Checklist for Docker Development

- [ ] Docker Desktop installed and running
- [ ] Navigated to project directory
- [ ] Ran `docker-compose up -d`
- [ ] All services showing as "Up"
- [ ] Web server accessible at http://localhost:8000
- [ ] Database connection working
- [ ] Redis connection working
- [ ] Can upload CSV files
- [ ] Worker processing jobs
- [ ] Logs accessible with `docker-compose logs`

---

## 🎯 Next Steps

### Local Development
```bash
# Work with Docker
docker-compose up -d
# Make changes, test, develop
docker-compose logs -f
```

### Deploy to Production
When ready, deploy to:
- **Render** (recommended): See RENDER_DEPLOYMENT.md
- **Heroku**: See DEPLOY_TO_HEROKU.md
- **Railway**: See deployment guides

---

## 📚 Additional Resources

- **Docker Docs**: https://docs.docker.com
- **Docker Compose Docs**: https://docs.docker.com/compose/
- **PostgreSQL Docs**: https://postgresql.org/docs/
- **Redis Docs**: https://redis.io/documentation

---

**🐳 Happy Dockering! Your complete local development environment is ready!**


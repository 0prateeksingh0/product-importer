# 🏗️ Architecture Documentation

## System Overview

The Product Importer is a distributed web application designed to efficiently handle large-scale product data imports with real-time progress tracking and webhook notifications.

```
┌─────────────────────────────────────────────────────────────┐
│                         Client Browser                       │
│                      (HTML/CSS/JavaScript)                   │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  │ HTTP/HTTPS
                  │ Server-Sent Events (SSE)
                  │
┌─────────────────▼───────────────────────────────────────────┐
│                    FastAPI Web Server                        │
│                    (Python/Uvicorn)                          │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ REST API Endpoints                                    │  │
│  │ • Product CRUD                                        │  │
│  │ • Import Management                                   │  │
│  │ • Webhook Configuration                               │  │
│  │ • Real-time Progress (SSE)                            │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────┬─────────────────────────┬─────────────────────┘
              │                         │
              │                         │ Async Tasks
              │ Database Queries        │
              │                         │
┌─────────────▼─────────────┐  ┌────────▼──────────────────────┐
│    PostgreSQL Database    │  │    Redis (Message Broker)     │
│                           │  │                               │
│ • Products                │  │ • Task Queue                  │
│ • Webhooks                │  │ • Result Backend              │
│ • Import Jobs             │  │ • Session Storage             │
└───────────────────────────┘  └────────┬──────────────────────┘
                                        │
                                        │ Task Processing
                                        │
                              ┌─────────▼──────────────────────┐
                              │   Celery Worker Processes      │
                              │                                │
                              │ • CSV Processing               │
                              │ • Batch Imports                │
                              │ • Webhook Triggers             │
                              │ • Background Tasks             │
                              └────────────────────────────────┘
                                        │
                                        │ HTTP POST
                                        │
                              ┌─────────▼──────────────────────┐
                              │    External Webhook Endpoints  │
                              │    (Third-party Services)      │
                              └────────────────────────────────┘
```

## Component Details

### 1. Frontend Layer (Client)

**Technology**: Vanilla JavaScript, HTML5, CSS3

**Responsibilities**:
- User interface rendering
- File upload handling
- Real-time progress display via SSE
- CRUD operations for products and webhooks
- Search, filtering, pagination
- Modal dialogs and notifications

**Key Features**:
- Single-page application (SPA) behavior with tabs
- Drag-and-drop file upload
- Real-time updates without polling (SSE)
- Responsive design for mobile/tablet
- Client-side validation

**Files**:
- `static/index.html` - Main UI structure
- `static/styles.css` - Modern CSS styling
- `static/script.js` - Application logic

---

### 2. API Layer (FastAPI)

**Technology**: FastAPI 0.104+, Python 3.11+, Uvicorn

**Responsibilities**:
- HTTP request handling
- Input validation (Pydantic)
- Business logic orchestration
- Database transactions
- SSE stream management
- Task delegation to Celery

**Key Endpoints**:

#### Products API
- `GET /api/products` - List with pagination/filtering
- `POST /api/products` - Create new product
- `GET /api/products/{id}` - Get single product
- `PUT /api/products/{id}` - Update product
- `DELETE /api/products/{id}` - Delete single product
- `DELETE /api/products` - Bulk delete all

#### Import API
- `POST /api/import` - Upload CSV file
- `GET /api/import/{job_id}` - Get import status
- `GET /api/import/{job_id}/stream` - SSE progress stream

#### Webhooks API
- `GET /api/webhooks` - List all webhooks
- `POST /api/webhooks` - Create webhook
- `GET /api/webhooks/{id}` - Get single webhook
- `PUT /api/webhooks/{id}` - Update webhook
- `DELETE /api/webhooks/{id}` - Delete webhook
- `POST /api/webhooks/{id}/test` - Test webhook

**Key Features**:
- Automatic API documentation (OpenAPI/Swagger)
- CORS middleware for cross-origin requests
- Request/response validation
- Error handling with detailed messages
- Static file serving

**Files**:
- `app/main.py` - FastAPI application and endpoints
- `app/schemas.py` - Pydantic models for validation
- `app/config.py` - Configuration management

---

### 3. Database Layer (PostgreSQL)

**Technology**: PostgreSQL 15+, SQLAlchemy 2.0 ORM

**Responsibilities**:
- Persistent data storage
- ACID transaction support
- Complex queries and aggregations
- Data integrity constraints
- Indexing for performance

**Schema Design**:

#### Products Table
```sql
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    sku VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(500) NOT NULL,
    description TEXT,
    price VARCHAR(50),
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX ix_products_sku ON products(sku);
CREATE INDEX ix_products_name ON products(name);
CREATE INDEX ix_products_active ON products(active);
CREATE UNIQUE INDEX ix_products_sku_lower ON products(LOWER(sku));
```

#### Webhooks Table
```sql
CREATE TABLE webhooks (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    url VARCHAR(1000) NOT NULL,
    event_type VARCHAR(100) NOT NULL,
    enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX ix_webhooks_event_type ON webhooks(event_type);
CREATE INDEX ix_webhooks_enabled ON webhooks(enabled);
```

#### Import Jobs Table
```sql
CREATE TABLE import_jobs (
    id VARCHAR(100) PRIMARY KEY,  -- UUID
    filename VARCHAR(500) NOT NULL,
    total_rows INTEGER DEFAULT 0,
    processed_rows INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    error_count INTEGER DEFAULT 0,
    status VARCHAR(50) DEFAULT 'pending',
    error_message TEXT,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);

-- Indexes
CREATE INDEX ix_import_jobs_status ON import_jobs(status);
```

**Key Features**:
- Functional index on `LOWER(sku)` for case-insensitive uniqueness
- Connection pooling (10 connections, 20 overflow)
- Automatic timestamp management
- Cascading updates/deletes where appropriate

**Files**:
- `app/database.py` - Database connection and session management
- `app/models.py` - SQLAlchemy ORM models

---

### 4. Task Queue Layer (Celery + Redis)

**Technology**: Celery 5.3, Redis 7

**Responsibilities**:
- Asynchronous task execution
- Long-running operation handling
- Background job processing
- Task result storage
- Distributed worker coordination

**Task Types**:

#### 1. CSV Import Task (`process_csv_import`)
- Reads CSV file in chunks
- Processes in batches (default: 1000 rows)
- Updates progress in database
- Handles duplicate SKUs (case-insensitive)
- Triggers completion webhooks
- Cleans up temporary files

**Workflow**:
```
1. Upload CSV → Save to disk
2. Create ImportJob record
3. Dispatch Celery task
4. Task reads CSV, counts rows
5. Process in batches:
   - Check for existing SKU (case-insensitive)
   - Insert new or update existing
   - Update progress in database
6. Mark job as completed/failed
7. Trigger webhooks
8. Clean up file
```

#### 2. Webhook Trigger Task (`trigger_webhooks`)
- Queries enabled webhooks for event type
- Sends HTTP POST with event payload
- Records success/failure
- Non-blocking execution
- Timeout protection (10 seconds)

**Configuration**:
```python
task_serializer = 'json'
result_serializer = 'json'
task_time_limit = 3600  # 1 hour max
task_soft_time_limit = 3300  # 55 minutes
worker_prefetch_multiplier = 1
worker_max_tasks_per_child = 1000
```

**Files**:
- `app/celery_app.py` - Celery configuration
- `app/tasks.py` - Task definitions

---

### 5. Real-time Communication (SSE)

**Technology**: Server-Sent Events, FastAPI StreamingResponse

**Purpose**: Provide real-time progress updates to client without polling

**Flow**:
```
1. Client uploads CSV
2. Server returns job_id immediately
3. Client opens SSE connection: /api/import/{job_id}/stream
4. Server streams updates every 0.5s while job is active
5. Updates include: status, progress %, rows processed, success/error counts
6. Connection closes when job completes/fails
7. Fallback to polling if SSE fails
```

**Advantages**:
- Lower latency than polling
- Reduced server load
- Native browser support
- Automatic reconnection
- Unidirectional (server → client)

**Data Format**:
```javascript
data: {
  "job_id": "uuid",
  "status": "processing",
  "total_rows": 50000,
  "processed_rows": 25000,
  "success_count": 24850,
  "error_count": 150,
  "progress": 50.0
}
```

---

## Data Flow Examples

### 1. CSV Import Flow

```
┌────────┐
│ Client │
└───┬────┘
    │
    │ 1. POST /api/import (CSV file)
    ▼
┌─────────────┐
│   FastAPI   │
└─────┬───────┘
      │
      │ 2. Save file to disk
      │ 3. Create ImportJob record
      ▼
┌──────────────┐     4. Read job_id     ┌────────────┐
│  PostgreSQL  │◄──────────────────────►│   Client   │
└──────────────┘                        └──────┬─────┘
      │                                        │
      │                                        │ 5. GET /api/import/{id}/stream
      │                                        ▼
      │                                 ┌────────────┐
      │ 6. Dispatch task               │  FastAPI   │
      │────────────────────────────────►│   (SSE)    │
      │                                 └──────┬─────┘
      ▼                                        │
┌───────────────┐                             │
│  Redis Queue  │                             │
└───────┬───────┘                             │
        │                                     │
        │ 7. Pick up task                    │
        ▼                                     │
┌────────────────┐                            │
│ Celery Worker  │                            │
└───────┬────────┘                            │
        │                                     │
        │ 8. Process CSV in batches          │
        │ 9. Update progress in DB           │
        ├─────────────────────────────────────┤
        │          10. Stream updates         │
        │◄────────────────────────────────────┤
        │                                     │
        │ 11. Complete job                   │
        ▼                                     │
┌──────────────┐                              │
│  PostgreSQL  │                              │
└──────┬───────┘                              │
       │                                      │
       │ 12. Notify completion                │
       └──────────────────────────────────────►
```

### 2. Product CRUD Flow

```
┌────────┐
│ Client │
└───┬────┘
    │
    │ 1. POST /api/products
    │    { sku, name, ... }
    ▼
┌─────────────┐
│   FastAPI   │
└─────┬───────┘
      │
      │ 2. Validate request (Pydantic)
      │ 3. Check SKU uniqueness (case-insensitive)
      ▼
┌──────────────┐
│  PostgreSQL  │
└──────┬───────┘
       │
       │ 4. Insert product
       │ 5. Return created product
       ▼
┌─────────────┐
│   FastAPI   │
└─────┬───────┘
      │
      │ 6. Dispatch webhook task
      ▼
┌───────────────┐
│  Redis Queue  │
└───────┬───────┘
        │
        │ 7. Process webhook
        ▼
┌────────────────┐
│ Celery Worker  │
└───────┬────────┘
        │
        │ 8. Query enabled webhooks for 'product.created'
        ▼
┌──────────────┐
│  PostgreSQL  │
└──────┬───────┘
       │
       │ 9. Found webhooks
       ▼
┌────────────────┐
│ Celery Worker  │
└───────┬────────┘
        │
        │ 10. POST to webhook URLs
        ▼
┌─────────────────┐
│ External APIs   │
└─────────────────┘
```

### 3. Webhook Event Flow

```
Event Triggers:
- product.created
- product.updated
- product.deleted
- import.completed
- products.bulk_deleted

┌─────────────┐
│  Any Event  │
└──────┬──────┘
       │
       │ trigger_webhooks.delay(event_type, data)
       ▼
┌───────────────┐
│  Redis Queue  │
└───────┬───────┘
        │
        ▼
┌────────────────┐
│ Celery Worker  │
└───────┬────────┘
        │
        │ Query webhooks WHERE event_type = ? AND enabled = true
        ▼
┌──────────────┐
│  PostgreSQL  │
└──────┬───────┘
       │
       │ Return matching webhooks
       ▼
┌────────────────┐
│ Celery Worker  │
└───────┬────────┘
        │
        │ For each webhook:
        │   POST {event, timestamp, data}
        │   Timeout: 10s
        ▼
┌─────────────────┐
│ External URLs   │
└─────────────────┘
```

---

## Performance Optimizations

### 1. Database Level
- **Indexing**: Multi-column indexes on frequently queried fields
- **Connection Pooling**: Reuse database connections (10 pool, 20 overflow)
- **Batch Operations**: Insert/update in batches of 1000
- **Functional Index**: `LOWER(sku)` for case-insensitive uniqueness

### 2. Application Level
- **Async Processing**: Celery for long-running operations
- **Pagination**: Limit query results (default: 50 per page)
- **Debouncing**: Client-side search debounce (300ms)
- **Lazy Loading**: Load data only when tab is active

### 3. Network Level
- **SSE**: Efficient real-time updates vs. polling
- **Compression**: Enable gzip in production
- **CDN**: Serve static assets from CDN (production)
- **Caching**: Redis for frequently accessed data

### 4. Scalability
- **Horizontal Scaling**: Add more web servers behind load balancer
- **Worker Scaling**: Add more Celery workers for concurrent imports
- **Database Replication**: Read replicas for high-traffic scenarios
- **Task Prioritization**: Prioritize interactive requests over background tasks

---

## Security Considerations

### 1. Input Validation
- Pydantic schemas for all API inputs
- File type validation (CSV only)
- Size limits on uploads (100MB default)
- SQL injection prevention (SQLAlchemy ORM)

### 2. Data Protection
- SKU case-insensitive uniqueness
- Transaction rollback on errors
- Data sanitization before display

### 3. Network Security
- CORS configuration
- HTTPS in production
- Webhook URL validation
- Rate limiting (to be implemented)

### 4. Authentication (To Be Added)
- JWT tokens
- Role-based access control
- API key authentication

---

## Error Handling Strategy

### 1. API Layer
- HTTP status codes (200, 201, 400, 404, 500)
- Detailed error messages
- Validation errors with field-level details

### 2. Worker Layer
- Task retry with exponential backoff
- Error logging
- Job status tracking (pending, processing, completed, failed)
- Error message storage

### 3. Database Layer
- Transaction rollback on error
- Constraint violation handling
- Connection timeout handling

### 4. Client Layer
- Toast notifications for user feedback
- Confirmation dialogs for destructive actions
- Graceful degradation (SSE → polling fallback)

---

## Monitoring and Observability

### Logs
- Application logs (FastAPI)
- Worker logs (Celery)
- Database query logs (optional)

### Metrics to Track
- Request count and latency
- Import job duration
- Success/error rates
- Database connection pool usage
- Celery queue length
- Webhook response times

### Recommended Tools
- **Error Tracking**: Sentry
- **APM**: New Relic, DataDog
- **Logs**: CloudWatch, Papertrail
- **Uptime**: UptimeRobot, Pingdom

---

## Future Enhancements

### Short Term
- [ ] User authentication and authorization
- [ ] API rate limiting
- [ ] CSV validation before import
- [ ] Export products to CSV
- [ ] Duplicate product detection report

### Medium Term
- [ ] Bulk product operations (update, activate/deactivate)
- [ ] Product categories and tags
- [ ] Advanced search (full-text, faceted)
- [ ] Import scheduling (cron jobs)
- [ ] Email notifications

### Long Term
- [ ] Multi-tenant support
- [ ] Product image uploads
- [ ] Inventory management
- [ ] Order management integration
- [ ] Analytics dashboard
- [ ] GraphQL API
- [ ] Mobile app (React Native)

---

## Technology Choices Rationale

### Why FastAPI?
- Modern, fast, async-capable
- Automatic API documentation
- Type hints and validation
- Growing ecosystem

### Why PostgreSQL?
- Robust and reliable
- Excellent JSON support
- Advanced indexing (functional, partial)
- Strong ACID compliance

### Why Celery?
- Battle-tested for async tasks
- Flexible worker scaling
- Multiple broker support
- Monitoring tools (Flower)

### Why Redis?
- Fast message broker
- Result backend
- Caching capabilities
- Simple setup

### Why Vanilla JavaScript?
- No build process needed
- Fast development
- Small bundle size
- Easy to understand and maintain

---

## Developer Workflow

### Local Development
1. Start services: `docker-compose up`
2. Make code changes
3. Changes auto-reload (FastAPI --reload)
4. Test in browser
5. Check logs: `docker-compose logs -f`

### Database Changes
1. Modify `app/models.py`
2. Restart services (tables auto-create)
3. For migrations: Use Alembic (future enhancement)

### Testing
1. Manual testing with sample CSV
2. API testing with cURL or Postman
3. Webhook testing with webhook.site
4. Browser testing (Chrome DevTools)

### Deployment
1. Push to Git repository
2. Platform auto-deploys (Heroku, Render, etc.)
3. Run smoke tests
4. Monitor logs for errors

---

## Conclusion

This architecture provides a solid foundation for a scalable, maintainable product import system. The separation of concerns, async processing, and real-time updates ensure excellent user experience even with large datasets.

For questions or suggestions, contact: [your-email@example.com]


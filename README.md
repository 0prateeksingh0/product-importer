# 🚀 Product Importer - Acme Inc.

A high-performance web application for importing and managing products from CSV files. Built with FastAPI, PostgreSQL, Celery, and Redis. Designed to handle up to 500,000 records efficiently with real-time progress tracking.

## ✨ Features

### 📤 **Story 1 - File Upload via UI**
- Upload large CSV files (up to 500,000+ products) through an intuitive web interface
- Real-time progress indicator with percentage, progress bar, and detailed statistics
- Automatic duplicate handling with case-insensitive SKU matching
- Unique SKU constraint enforcement
- Support for active/inactive product status
- Optimized for large file processing with batch operations

### 📊 **Story 1A - Upload Progress Visibility**
- Real-time progress updates via Server-Sent Events (SSE)
- Visual progress bar with percentage completion
- Live statistics: total rows, processed, success count, error count
- Clear status messages (Parsing, Validating, Import Complete)
- Error handling with detailed failure messages and retry capability
- Automatic fallback to polling if SSE is unavailable

### 📦 **Story 2 - Product Management UI**
- Complete CRUD operations for products
- Advanced filtering by SKU, name, active status, or description
- Paginated product listings with customizable page sizes
- Inline editing with modal forms
- Deletion with confirmation dialogs
- Clean, modern, responsive design
- Real-time search with debouncing

### 🗑️ **Story 3 - Bulk Delete from UI**
- Delete all products with a single action
- Protected with confirmation dialog
- Success/failure notifications
- Visual feedback during processing
- Maintains database integrity

### 🔗 **Story 4 - Webhook Configuration via UI**
- Add, edit, test, and delete webhooks through the UI
- Support for multiple event types:
  - `product.created`
  - `product.updated`
  - `product.deleted`
  - `import.completed`
  - `products.bulk_deleted`
- Enable/disable webhooks without deletion
- Test webhooks with response code and timing feedback
- Non-blocking webhook processing

## 🛠️ Tech Stack

- **Web Framework**: FastAPI 0.104+ (Python 3.11)
- **Database**: PostgreSQL 15
- **Asynchronous Processing**: Celery 5.3 with Redis
- **ORM**: SQLAlchemy 2.0
- **Real-time Updates**: Server-Sent Events (SSE)
- **Frontend**: Vanilla JavaScript, HTML5, CSS3
- **Deployment**: Docker & Docker Compose

## 📋 Prerequisites

- Docker Desktop (recommended) OR
- Python 3.11+, PostgreSQL 15+, Redis 7+

## 🚀 Quick Start

### Option 1: Docker (Recommended)

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd "Product Importer"
   ```

2. **Run the application**
   ```bash
   chmod +x run.sh
   ./run.sh
   ```

3. **Access the application**
   - Web UI: http://localhost:8000
   - API Docs: http://localhost:8000/docs

### Option 2: Manual Setup

1. **Install dependencies**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Set up environment**
   ```bash
   cp env.example .env
   # Edit .env with your database and Redis URLs
   ```

3. **Start PostgreSQL and Redis**
   ```bash
   # Using Docker
   docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=postgres postgres:15
   docker run -d -p 6379:6379 redis:7-alpine
   ```

4. **Run the application**
   ```bash
   # Terminal 1: FastAPI server
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   
   # Terminal 2: Celery worker
   celery -A app.celery_app worker --loglevel=info
   ```

## 📖 Usage Guide

### Importing Products

1. Navigate to the **Import Products** tab
2. Click or drag-and-drop a CSV file
3. Watch the real-time progress updates
4. View success/error statistics upon completion

**CSV Format:**
```csv
sku,name,description,price
SKU001,Product Name,Product description,29.99
```

**Required fields**: `sku`, `name`  
**Optional fields**: `description`, `price`

A sample CSV file (`sample_products.csv`) is included for testing.

### Managing Products

1. Navigate to the **Manage Products** tab
2. Use the search bar to filter products
3. Click **Add Product** to create new products
4. Click **Edit** on any product to modify it
5. Click **Delete** to remove a product (with confirmation)
6. Click **Delete All** to remove all products (with confirmation)

### Configuring Webhooks

1. Navigate to the **Webhooks** tab
2. Click **Add Webhook**
3. Fill in the webhook details:
   - Name: Friendly identifier
   - URL: Target endpoint (e.g., https://webhook.site/unique-id)
   - Event Type: Select the triggering event
   - Enabled: Toggle active status
4. Click **Test** to send a test payload
5. View response code and timing

**Test Webhook URL**: Use https://webhook.site to create a test endpoint

## 🏗️ Architecture

### Database Models

**Product**
- `id`: Primary key
- `sku`: Unique, case-insensitive (indexed)
- `name`: Product name (indexed)
- `description`: Optional text
- `price`: Optional price string
- `active`: Boolean status (default: true, indexed)
- `created_at`, `updated_at`: Timestamps

**Webhook**
- `id`: Primary key
- `name`: Webhook name
- `url`: Target URL
- `event_type`: Event trigger (indexed)
- `enabled`: Active status (indexed)
- `created_at`, `updated_at`: Timestamps

**ImportJob**
- `id`: UUID (job identifier)
- `filename`: Original file name
- `total_rows`, `processed_rows`: Progress tracking
- `success_count`, `error_count`: Statistics
- `status`: pending | processing | completed | failed
- `error_message`: Failure details
- `started_at`, `completed_at`: Timestamps

### API Endpoints

#### Products
- `GET /api/products` - List products (paginated, filterable)
- `GET /api/products/{id}` - Get single product
- `POST /api/products` - Create product
- `PUT /api/products/{id}` - Update product
- `DELETE /api/products/{id}` - Delete product
- `DELETE /api/products` - Bulk delete all products

#### Import
- `POST /api/import` - Upload CSV file
- `GET /api/import/{job_id}` - Get import status
- `GET /api/import/{job_id}/stream` - Stream progress (SSE)

#### Webhooks
- `GET /api/webhooks` - List webhooks
- `GET /api/webhooks/{id}` - Get single webhook
- `POST /api/webhooks` - Create webhook
- `PUT /api/webhooks/{id}` - Update webhook
- `DELETE /api/webhooks/{id}` - Delete webhook
- `POST /api/webhooks/{id}/test` - Test webhook

#### Health
- `GET /api/health` - Health check

## 🎯 Performance Optimizations

1. **Batch Processing**: CSV imports processed in configurable batches (default: 1000 rows)
2. **Database Indexing**: Functional index on lowercase SKU for case-insensitive lookups
3. **Connection Pooling**: SQLAlchemy connection pool (size: 10, overflow: 20)
4. **Asynchronous Workers**: Celery handles long-running operations without blocking
5. **Real-time Updates**: SSE for efficient push-based progress updates
6. **Efficient Queries**: Pagination and filtering at database level

## 🚢 Deployment

### Heroku

```bash
# Install Heroku CLI and login
heroku login

# Create app
heroku create product-importer-acme

# Add PostgreSQL and Redis
heroku addons:create heroku-postgresql:mini
heroku addons:create heroku-redis:mini

# Set buildpack
heroku buildpacks:set heroku/python

# Deploy
git push heroku main

# Scale workers
heroku ps:scale web=1 worker=1
```

**Important**: Add a `Procfile`:
```
web: uvicorn app.main:app --host 0.0.0.0 --port $PORT
worker: celery -A app.celery_app worker --loglevel=info
```

### Render

1. Create a new Web Service
2. Connect your repository
3. Set build command: `pip install -r requirements.txt`
4. Set start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Add PostgreSQL and Redis services
6. Add environment variables from `.env`
7. Add a Background Worker for Celery

### AWS / GCP / Azure

Use the included `Dockerfile` and `docker-compose.yml` for containerized deployment.

## 🧪 Testing

### Manual Testing with Sample Data

1. Start the application
2. Upload `sample_products.csv` from the Import tab
3. Watch real-time progress
4. Navigate to Manage Products to verify import
5. Test CRUD operations
6. Set up a test webhook at https://webhook.site
7. Trigger events and verify webhook calls

### API Testing with cURL

```bash
# Health check
curl http://localhost:8000/api/health

# List products
curl http://localhost:8000/api/products

# Create product
curl -X POST http://localhost:8000/api/products \
  -H "Content-Type: application/json" \
  -d '{"sku":"TEST001","name":"Test Product","active":true}'

# Upload CSV
curl -X POST http://localhost:8000/api/import \
  -F "file=@sample_products.csv"
```

## 📝 Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://postgres:postgres@localhost:5432/product_importer` |
| `REDIS_URL` | Redis connection string | `redis://localhost:6379/0` |
| `CELERY_BROKER_URL` | Celery broker URL | `redis://localhost:6379/0` |
| `CELERY_RESULT_BACKEND` | Celery result backend | `redis://localhost:6379/0` |
| `SECRET_KEY` | Application secret key | `dev-secret-key-change-in-production` |
| `DEBUG` | Debug mode | `True` |
| `ALLOWED_ORIGINS` | CORS allowed origins | `http://localhost:8000` |
| `MAX_UPLOAD_SIZE` | Max file size in bytes | `104857600` (100MB) |
| `BATCH_SIZE` | Rows per batch | `1000` |

## 🔒 Security Considerations

- Change `SECRET_KEY` in production
- Use secure passwords for PostgreSQL
- Enable HTTPS in production
- Implement authentication/authorization for production use
- Validate webhook URLs before saving
- Rate limit API endpoints
- Sanitize CSV inputs

## 🐛 Troubleshooting

### Import stuck at "Processing"
- Check Celery worker logs: `docker-compose logs celery_worker`
- Verify Redis is running: `docker-compose ps redis`
- Check for CSV formatting issues

### Database connection errors
- Verify PostgreSQL is running: `docker-compose ps db`
- Check DATABASE_URL in .env
- Ensure database migrations ran successfully

### Webhooks not firing
- Verify webhook is enabled
- Check Celery worker logs
- Test webhook URL is accessible
- Check network/firewall settings

## 📊 Project Structure

```
Product Importer/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration settings
│   ├── database.py          # Database setup
│   ├── models.py            # SQLAlchemy models
│   ├── schemas.py           # Pydantic schemas
│   ├── celery_app.py        # Celery configuration
│   └── tasks.py             # Celery tasks
├── static/
│   ├── index.html           # Frontend UI
│   ├── styles.css           # Styling
│   └── script.js            # JavaScript logic
├── uploads/                 # Temporary CSV storage
├── requirements.txt         # Python dependencies
├── Dockerfile               # Docker image definition
├── docker-compose.yml       # Multi-container setup
├── run.sh                   # Quick start script
├── env.example              # Environment template
├── sample_products.csv      # Sample data
└── README.md                # This file
```

## 🎓 Code Quality

- **Clean Code**: Well-documented, readable code following PEP 8
- **Separation of Concerns**: Clear separation between API, business logic, and data layers
- **Error Handling**: Comprehensive error handling with user-friendly messages
- **Type Hints**: Full type annotations for better IDE support
- **Comments**: Meaningful comments explaining complex logic
- **Modularity**: Reusable components and functions

## 📜 License

This project is created for Acme Inc. as part of a technical assessment.

## 👤 Author

Created by [Your Name] using AI-assisted development with Claude (Anthropic) and Cursor IDE.

## 🙏 Acknowledgments

- FastAPI for the excellent web framework
- SQLAlchemy for powerful ORM capabilities
- Celery for reliable distributed task processing
- PostgreSQL for robust data storage
- Redis for fast in-memory caching

---



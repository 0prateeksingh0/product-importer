"""
FastAPI main application with all API endpoints.
"""
import uuid
import os
from typing import Optional, List
from datetime import datetime
from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
import httpx
import asyncio

from app.config import settings
from app.database import get_db, init_db
from app.models import Product, Webhook, ImportJob
from app.schemas import (
    Product as ProductSchema,
    ProductCreate,
    ProductUpdate,
    ProductList,
    Webhook as WebhookSchema,
    WebhookCreate,
    WebhookUpdate,
    WebhookTestResponse,
    ImportJobStatus,
    MessageResponse,
    BulkDeleteResponse
)
from app.tasks import process_csv_import, trigger_webhooks

# Initialize FastAPI app
app = FastAPI(
    title="Product Importer API",
    description="API for importing and managing products from CSV files",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create static directory for frontend
os.makedirs("static", exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    init_db()


# ============================================================================
# PRODUCT ENDPOINTS
# ============================================================================

@app.get("/api/products", response_model=ProductList)
def get_products(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=1000, description="Items per page"),
    search: Optional[str] = Query(None, description="Search in SKU, name, or description"),
    active: Optional[bool] = Query(None, description="Filter by active status"),
    db: Session = Depends(get_db)
):
    """
    Get paginated list of products with optional filtering.
    """
    query = db.query(Product)
    
    # Apply search filter
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Product.sku.ilike(search_term),
                Product.name.ilike(search_term),
                Product.description.ilike(search_term)
            )
        )
    
    # Apply active filter
    if active is not None:
        query = query.filter(Product.active == active)
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    offset = (page - 1) * page_size
    items = query.order_by(Product.created_at.desc()).offset(offset).limit(page_size).all()
    
    # Calculate total pages
    pages = (total + page_size - 1) // page_size
    
    return ProductList(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=pages
    )


@app.get("/api/products/{product_id}", response_model=ProductSchema)
def get_product(product_id: int, db: Session = Depends(get_db)):
    """Get a single product by ID."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@app.post("/api/products", response_model=ProductSchema, status_code=status.HTTP_201_CREATED)
def create_product(product: ProductCreate, db: Session = Depends(get_db)):
    """Create a new product."""
    # Check for duplicate SKU (case-insensitive)
    existing = db.query(Product).filter(
        func.lower(Product.sku) == func.lower(product.sku)
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Product with SKU '{product.sku}' already exists"
        )
    
    db_product = Product(**product.model_dump())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    
    # Trigger webhooks
    trigger_webhooks.delay('product.created', {
        'product_id': db_product.id,
        'sku': db_product.sku,
        'name': db_product.name
    })
    
    return db_product


@app.put("/api/products/{product_id}", response_model=ProductSchema)
def update_product(
    product_id: int,
    product: ProductUpdate,
    db: Session = Depends(get_db)
):
    """Update an existing product."""
    db_product = db.query(Product).filter(Product.id == product_id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Check for SKU conflicts if SKU is being updated
    if product.sku and product.sku != db_product.sku:
        existing = db.query(Product).filter(
            func.lower(Product.sku) == func.lower(product.sku),
            Product.id != product_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Product with SKU '{product.sku}' already exists"
            )
    
    # Update fields
    update_data = product.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_product, field, value)
    
    db.commit()
    db.refresh(db_product)
    
    # Trigger webhooks
    trigger_webhooks.delay('product.updated', {
        'product_id': db_product.id,
        'sku': db_product.sku,
        'name': db_product.name
    })
    
    return db_product


@app.delete("/api/products/{product_id}", response_model=MessageResponse)
def delete_product(product_id: int, db: Session = Depends(get_db)):
    """Delete a product."""
    db_product = db.query(Product).filter(Product.id == product_id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    sku = db_product.sku
    db.delete(db_product)
    db.commit()
    
    # Trigger webhooks
    trigger_webhooks.delay('product.deleted', {
        'product_id': product_id,
        'sku': sku
    })
    
    return MessageResponse(message="Product deleted successfully")


@app.delete("/api/products", response_model=BulkDeleteResponse)
def bulk_delete_products(db: Session = Depends(get_db)):
    """Delete all products (with confirmation in UI)."""
    count = db.query(Product).count()
    db.query(Product).delete()
    db.commit()
    
    # Trigger webhooks
    trigger_webhooks.delay('products.bulk_deleted', {
        'deleted_count': count
    })
    
    return BulkDeleteResponse(
        deleted_count=count,
        message=f"Successfully deleted {count} products"
    )


# ============================================================================
# IMPORT ENDPOINTS
# ============================================================================

@app.post("/api/import", response_model=ImportJobStatus, status_code=status.HTTP_202_ACCEPTED)
async def upload_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload a CSV file for import processing.
    Returns immediately with job ID for progress tracking.
    """
    # Validate file type
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV")
    
    # Generate unique job ID
    job_id = str(uuid.uuid4())
    
    # Save file temporarily
    file_path = os.path.join(settings.UPLOAD_DIR, f"{job_id}.csv")
    
    try:
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")
    
    # Create import job record
    import_job = ImportJob(
        id=job_id,
        filename=file.filename,
        status="pending"
    )
    db.add(import_job)
    db.commit()
    db.refresh(import_job)
    
    # Start async processing
    process_csv_import.delay(job_id, file_path)
    
    return import_job


@app.get("/api/import/{job_id}", response_model=ImportJobStatus)
def get_import_status(job_id: str, db: Session = Depends(get_db)):
    """Get the status of an import job."""
    job = db.query(ImportJob).filter(ImportJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Import job not found")
    return job


@app.get("/api/import/{job_id}/stream")
async def stream_import_progress(job_id: str, db: Session = Depends(get_db)):
    """
    Stream import progress using Server-Sent Events (SSE).
    """
    async def event_generator():
        """Generate SSE events with import progress."""
        last_processed = -1
        
        while True:
            # Get current job status
            job = db.query(ImportJob).filter(ImportJob.id == job_id).first()
            
            if not job:
                yield f"data: {{'error': 'Job not found'}}\n\n"
                break
            
            # Only send update if progress changed
            if job.processed_rows != last_processed or job.status in ['completed', 'failed']:
                progress = 0
                if job.total_rows > 0:
                    progress = round((job.processed_rows / job.total_rows) * 100, 2)
                
                data = {
                    'job_id': job.id,
                    'status': job.status,
                    'processed_rows': job.processed_rows,
                    'total_rows': job.total_rows,
                    'success_count': job.success_count,
                    'error_count': job.error_count,
                    'progress': progress,
                    'error_message': job.error_message
                }
                
                yield f"data: {data}\n\n"
                last_processed = job.processed_rows
                
                # Stop streaming if job is complete or failed
                if job.status in ['completed', 'failed']:
                    break
            
            # Wait before next check
            await asyncio.sleep(0.5)
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


# ============================================================================
# WEBHOOK ENDPOINTS
# ============================================================================

@app.get("/api/webhooks", response_model=List[WebhookSchema])
def get_webhooks(db: Session = Depends(get_db)):
    """Get all configured webhooks."""
    return db.query(Webhook).order_by(Webhook.created_at.desc()).all()


@app.get("/api/webhooks/{webhook_id}", response_model=WebhookSchema)
def get_webhook(webhook_id: int, db: Session = Depends(get_db)):
    """Get a single webhook by ID."""
    webhook = db.query(Webhook).filter(Webhook.id == webhook_id).first()
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")
    return webhook


@app.post("/api/webhooks", response_model=WebhookSchema, status_code=status.HTTP_201_CREATED)
def create_webhook(webhook: WebhookCreate, db: Session = Depends(get_db)):
    """Create a new webhook."""
    db_webhook = Webhook(**webhook.model_dump())
    db.add(db_webhook)
    db.commit()
    db.refresh(db_webhook)
    return db_webhook


@app.put("/api/webhooks/{webhook_id}", response_model=WebhookSchema)
def update_webhook(
    webhook_id: int,
    webhook: WebhookUpdate,
    db: Session = Depends(get_db)
):
    """Update an existing webhook."""
    db_webhook = db.query(Webhook).filter(Webhook.id == webhook_id).first()
    if not db_webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")
    
    update_data = webhook.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_webhook, field, value)
    
    db.commit()
    db.refresh(db_webhook)
    return db_webhook


@app.delete("/api/webhooks/{webhook_id}", response_model=MessageResponse)
def delete_webhook(webhook_id: int, db: Session = Depends(get_db)):
    """Delete a webhook."""
    db_webhook = db.query(Webhook).filter(Webhook.id == webhook_id).first()
    if not db_webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")
    
    db.delete(db_webhook)
    db.commit()
    return MessageResponse(message="Webhook deleted successfully")


@app.post("/api/webhooks/{webhook_id}/test", response_model=WebhookTestResponse)
async def test_webhook(webhook_id: int, db: Session = Depends(get_db)):
    """Test a webhook by sending a test payload."""
    webhook = db.query(Webhook).filter(Webhook.id == webhook_id).first()
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")
    
    test_payload = {
        'event': 'webhook.test',
        'timestamp': datetime.utcnow().isoformat(),
        'data': {
            'message': 'This is a test webhook',
            'webhook_id': webhook_id
        }
    }
    
    try:
        start_time = asyncio.get_event_loop().time()
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(webhook.url, json=test_payload)
        response_time = asyncio.get_event_loop().time() - start_time
        
        return WebhookTestResponse(
            success=response.status_code < 400,
            status_code=response.status_code,
            response_time=round(response_time, 3)
        )
    except Exception as e:
        return WebhookTestResponse(
            success=False,
            error=str(e)
        )


# ============================================================================
# HEALTH CHECK
# ============================================================================

@app.get("/api/health")
def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }


# ============================================================================
# FRONTEND
# ============================================================================

@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main frontend page."""
    try:
        with open("static/index.html", "r") as f:
            return f.read()
    except FileNotFoundError:
        return """
        <html>
            <head><title>Product Importer</title></head>
            <body>
                <h1>Product Importer API</h1>
                <p>API is running. Frontend not yet deployed.</p>
                <p>Visit <a href="/docs">/docs</a> for API documentation.</p>
            </body>
        </html>
        """


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


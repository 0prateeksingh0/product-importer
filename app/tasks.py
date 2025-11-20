"""
Celery tasks for asynchronous processing.
"""
import os
import csv
import time
from datetime import datetime
from typing import Dict, Any
from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert
from celery import Task
import httpx

from app.celery_app import celery_app
from app.database import SessionLocal
from app.models import Product, ImportJob, Webhook
from app.config import settings


class DatabaseTask(Task):
    """Base task that provides database session."""
    _db = None

    @property
    def db(self):
        if self._db is None:
            self._db = SessionLocal()
        return self._db

    def after_return(self, *args, **kwargs):
        if self._db is not None:
            self._db.close()
            self._db = None


@celery_app.task(bind=True, base=DatabaseTask)
def process_csv_import(self, job_id: str, file_path: str):
    """
    Process CSV file import asynchronously.
    
    Args:
        job_id: Unique identifier for this import job
        file_path: Path to the uploaded CSV file
    """
    db = self.db
    
    try:
        # Update job status to processing
        job = db.query(ImportJob).filter(ImportJob.id == job_id).first()
        if not job:
            raise Exception(f"Import job {job_id} not found")
        
        job.status = "processing"
        db.commit()
        
        # Read and validate CSV
        if not os.path.exists(file_path):
            raise Exception(f"File not found: {file_path}")
        
        # Count total rows first (excluding header)
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            total_rows = sum(1 for _ in csv.DictReader(f))
        
        job.total_rows = total_rows
        db.commit()
        
        # Process CSV in batches
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            
            # Validate CSV headers
            required_fields = ['sku', 'name']
            if not all(field in reader.fieldnames for field in required_fields):
                raise Exception(f"CSV must contain columns: {', '.join(required_fields)}")
            
            batch = []
            processed = 0
            success_count = 0
            error_count = 0
            
            for row in reader:
                try:
                    # Prepare product data
                    sku = row.get('sku', '').strip()
                    if not sku:
                        error_count += 1
                        continue
                    
                    product_data = {
                        'sku': sku,
                        'name': row.get('name', '').strip(),
                        'description': row.get('description', '').strip() or None,
                        'price': row.get('price', '').strip() or None,
                        'active': True  # Default to active
                    }
                    
                    batch.append(product_data)
                    
                    # Process batch when it reaches the batch size
                    if len(batch) >= settings.BATCH_SIZE:
                        success, errors = _process_batch(db, batch)
                        success_count += success
                        error_count += errors
                        processed += len(batch)
                        
                        # Update progress
                        job.processed_rows = processed
                        job.success_count = success_count
                        job.error_count = error_count
                        db.commit()
                        
                        batch = []
                    
                except Exception as e:
                    print(f"Error processing row: {e}")
                    error_count += 1
            
            # Process remaining batch
            if batch:
                success, errors = _process_batch(db, batch)
                success_count += success
                error_count += errors
                processed += len(batch)
        
        # Update job as completed
        job.processed_rows = processed
        job.success_count = success_count
        job.error_count = error_count
        job.status = "completed"
        job.completed_at = datetime.utcnow()
        db.commit()
        
        # Trigger webhooks for import completion
        trigger_webhooks.delay('import.completed', {
            'job_id': job_id,
            'total_rows': total_rows,
            'success_count': success_count,
            'error_count': error_count
        })
        
        # Clean up file
        try:
            os.remove(file_path)
        except:
            pass
        
        return {
            'status': 'completed',
            'processed': processed,
            'success': success_count,
            'errors': error_count
        }
        
    except Exception as e:
        # Update job as failed
        job = db.query(ImportJob).filter(ImportJob.id == job_id).first()
        if job:
            job.status = "failed"
            job.error_message = str(e)
            job.completed_at = datetime.utcnow()
            db.commit()
        
        raise e


def _process_batch(db, batch: list) -> tuple:
    """
    Process a batch of products using upsert (insert or update on conflict).
    
    Returns:
        Tuple of (success_count, error_count)
    """
    try:
        if not batch:
            return 0, 0
        
        # Use PostgreSQL's INSERT ... ON CONFLICT for efficient upserts
        # This handles case-insensitive SKU matching via the functional index
        for product_data in batch:
            # Check if product exists (case-insensitive)
            existing = db.query(Product).filter(
                func.lower(Product.sku) == func.lower(product_data['sku'])
            ).first()
            
            if existing:
                # Update existing product
                for key, value in product_data.items():
                    if key != 'sku':  # Don't update SKU
                        setattr(existing, key, value)
            else:
                # Create new product
                new_product = Product(**product_data)
                db.add(new_product)
        
        db.commit()
        return len(batch), 0
        
    except Exception as e:
        db.rollback()
        print(f"Error processing batch: {e}")
        return 0, len(batch)


@celery_app.task(bind=True, base=DatabaseTask)
def trigger_webhooks(self, event_type: str, data: Dict[str, Any]):
    """
    Trigger all enabled webhooks for a specific event type.
    
    Args:
        event_type: The type of event (e.g., 'product.created', 'import.completed')
        data: Event data to send in webhook payload
    """
    db = self.db
    
    # Get all enabled webhooks for this event type
    webhooks = db.query(Webhook).filter(
        Webhook.event_type == event_type,
        Webhook.enabled == True
    ).all()
    
    if not webhooks:
        return {'message': 'No webhooks configured for this event'}
    
    results = []
    
    for webhook in webhooks:
        try:
            payload = {
                'event': event_type,
                'timestamp': datetime.utcnow().isoformat(),
                'data': data
            }
            
            with httpx.Client(timeout=10.0) as client:
                response = client.post(webhook.url, json=payload)
                results.append({
                    'webhook_id': webhook.id,
                    'success': response.status_code < 400,
                    'status_code': response.status_code
                })
        except Exception as e:
            results.append({
                'webhook_id': webhook.id,
                'success': False,
                'error': str(e)
            })
    
    return results


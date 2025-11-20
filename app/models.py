"""
SQLAlchemy database models for the Product Importer application.
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Index
from sqlalchemy.sql import func
from app.database import Base


class Product(Base):
    """
    Product model representing items in the catalog.
    
    Attributes:
        id: Primary key
        sku: Stock Keeping Unit (unique, case-insensitive)
        name: Product name
        description: Product description
        price: Product price as string (can be formatted as needed)
        active: Whether the product is active (default: True)
        created_at: Timestamp when product was created
        updated_at: Timestamp when product was last updated
    """
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    sku = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(500), nullable=False, index=True)
    description = Column(Text, nullable=True)
    price = Column(String(50), nullable=True)
    active = Column(Boolean, default=True, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Create a functional index for case-insensitive SKU lookups
    __table_args__ = (
        Index('ix_products_sku_lower', func.lower(sku), unique=True),
    )

    def __repr__(self):
        return f"<Product(id={self.id}, sku='{self.sku}', name='{self.name}')>"


class Webhook(Base):
    """
    Webhook model for configuring external notifications.
    
    Attributes:
        id: Primary key
        name: Friendly name for the webhook
        url: Target URL for webhook POST requests
        event_type: Type of event that triggers this webhook
        enabled: Whether the webhook is active
        created_at: Timestamp when webhook was created
        updated_at: Timestamp when webhook was last updated
    """
    __tablename__ = "webhooks"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    url = Column(String(1000), nullable=False)
    event_type = Column(String(100), nullable=False, index=True)  # e.g., 'product.created', 'product.updated', 'import.completed'
    enabled = Column(Boolean, default=True, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<Webhook(id={self.id}, name='{self.name}', event='{self.event_type}')>"


class ImportJob(Base):
    """
    Import job tracking for CSV uploads.
    
    Attributes:
        id: Primary key (also used as job_id)
        filename: Original filename
        total_rows: Total number of rows to process
        processed_rows: Number of rows processed so far
        success_count: Number of successfully imported products
        error_count: Number of errors encountered
        status: Job status (pending, processing, completed, failed)
        error_message: Error message if job failed
        started_at: When the job started
        completed_at: When the job completed
    """
    __tablename__ = "import_jobs"

    id = Column(String(100), primary_key=True)  # UUID
    filename = Column(String(500), nullable=False)
    total_rows = Column(Integer, default=0)
    processed_rows = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    error_count = Column(Integer, default=0)
    status = Column(String(50), default="pending", nullable=False, index=True)  # pending, processing, completed, failed
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self):
        return f"<ImportJob(id='{self.id}', status='{self.status}', progress={self.processed_rows}/{self.total_rows})>"


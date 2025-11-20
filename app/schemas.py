"""
Pydantic schemas for request/response validation.
"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, HttpUrl


# Product Schemas
class ProductBase(BaseModel):
    """Base product schema with common fields."""
    sku: str = Field(..., max_length=255, description="Stock Keeping Unit")
    name: str = Field(..., max_length=500, description="Product name")
    description: Optional[str] = Field(None, description="Product description")
    price: Optional[str] = Field(None, max_length=50, description="Product price")
    active: bool = Field(True, description="Whether the product is active")


class ProductCreate(ProductBase):
    """Schema for creating a new product."""
    pass


class ProductUpdate(BaseModel):
    """Schema for updating a product (all fields optional)."""
    sku: Optional[str] = Field(None, max_length=255)
    name: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = None
    price: Optional[str] = Field(None, max_length=50)
    active: Optional[bool] = None


class Product(ProductBase):
    """Schema for product responses."""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProductList(BaseModel):
    """Paginated product list response."""
    items: List[Product]
    total: int
    page: int
    page_size: int
    pages: int


# Webhook Schemas
class WebhookBase(BaseModel):
    """Base webhook schema."""
    name: str = Field(..., max_length=255, description="Webhook name")
    url: str = Field(..., max_length=1000, description="Target URL")
    event_type: str = Field(..., max_length=100, description="Event type that triggers webhook")
    enabled: bool = Field(True, description="Whether webhook is enabled")


class WebhookCreate(WebhookBase):
    """Schema for creating a webhook."""
    pass


class WebhookUpdate(BaseModel):
    """Schema for updating a webhook."""
    name: Optional[str] = Field(None, max_length=255)
    url: Optional[str] = Field(None, max_length=1000)
    event_type: Optional[str] = Field(None, max_length=100)
    enabled: Optional[bool] = None


class Webhook(WebhookBase):
    """Schema for webhook responses."""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class WebhookTestResponse(BaseModel):
    """Response from testing a webhook."""
    success: bool
    status_code: Optional[int] = None
    response_time: Optional[float] = None
    error: Optional[str] = None


# Import Job Schemas
class ImportJobStatus(BaseModel):
    """Import job status response."""
    id: str
    filename: str
    total_rows: int
    processed_rows: int
    success_count: int
    error_count: int
    status: str
    error_message: Optional[str] = None
    started_at: datetime
    completed_at: Optional[datetime] = None
    progress_percentage: float = 0.0

    class Config:
        from_attributes = True

    @property
    def progress_percentage(self) -> float:
        """Calculate progress percentage."""
        if self.total_rows == 0:
            return 0.0
        return round((self.processed_rows / self.total_rows) * 100, 2)


class ImportJobCreate(BaseModel):
    """Schema for starting an import job."""
    filename: str


# General Response Schemas
class MessageResponse(BaseModel):
    """Generic message response."""
    message: str
    detail: Optional[str] = None


class BulkDeleteResponse(BaseModel):
    """Response from bulk delete operation."""
    deleted_count: int
    message: str


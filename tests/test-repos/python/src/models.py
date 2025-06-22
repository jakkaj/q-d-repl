"""Data models for the analysis service."""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, validator
import json


class DataPoint(BaseModel):
    """Represents a single data point in our analysis."""
    
    id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    value: float
    category: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    is_valid: bool = True
    error_message: Optional[str] = None
    
    @validator('value')
    def validate_value(cls, v):
        if not isinstance(v, (int, float)):
            raise ValueError('Value must be numeric')
        if v < 0:
            raise ValueError('Value cannot be negative')
        return float(v)
    
    @validator('category')
    def validate_category(cls, v):
        allowed_categories = ['sales', 'marketing', 'operations', 'finance', 'other']
        if v.lower() not in allowed_categories:
            raise ValueError(f'Category must be one of: {allowed_categories}')
        return v.lower()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat(),
            'value': self.value,
            'category': self.category,
            'metadata': self.metadata,
            'is_valid': self.is_valid,
            'error_message': self.error_message
        }
    
    @classmethod
    def error(cls, id: str, category: str, error_message: str) -> 'DataPoint':
        """Create an error data point."""
        return cls(
            id=id,
            value=0.0,
            category=category,
            is_valid=False,
            error_message=error_message
        )


class AnalysisResult(BaseModel):
    """Results from data analysis operations."""
    
    total_points: int
    valid_points: int
    invalid_points: int
    categories: Dict[str, int]
    statistics: Dict[str, float]
    processing_time_ms: float
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    
    @property
    def success_rate(self) -> float:
        """Calculate the success rate of data processing."""
        if self.total_points == 0:
            return 0.0
        return (self.valid_points / self.total_points) * 100
    
    @property
    def summary(self) -> str:
        """Generate a human-readable summary."""
        return (
            f"Processed {self.total_points} data points "
            f"({self.valid_points} valid, {self.invalid_points} invalid) "
            f"in {self.processing_time_ms:.2f}ms. "
            f"Success rate: {self.success_rate:.1f}%"
        )


class ProcessingConfig(BaseModel):
    """Configuration for data processing operations."""
    
    batch_size: int = Field(default=100, ge=1, le=10000)
    parallel_workers: int = Field(default=4, ge=1, le=32)
    timeout_seconds: int = Field(default=30, ge=1, le=300)
    enable_caching: bool = True
    cache_ttl_seconds: int = Field(default=3600, ge=60)
    validate_data: bool = True
    retry_failed: bool = True
    max_retries: int = Field(default=3, ge=0, le=10)
    
    @validator('parallel_workers')
    def validate_workers(cls, v, values):
        batch_size = values.get('batch_size', 100)
        if v > batch_size:
            raise ValueError('Workers cannot exceed batch size')
        return v
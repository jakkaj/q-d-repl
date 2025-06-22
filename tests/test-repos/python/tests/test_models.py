"""Unit tests for data models."""

import pytest
from datetime import datetime, timedelta
from pydantic import ValidationError

from src.models import DataPoint, AnalysisResult, ProcessingConfig


class TestDataPoint:
    """Test the DataPoint model."""
    
    def test_valid_data_point_creation(self):
        """Test creating a valid data point."""
        data_point = DataPoint(
            id="test-1",
            value=42.5,
            category="sales",
            metadata={"source": "test"}
        )
        
        assert data_point.id == "test-1"
        assert data_point.value == 42.5
        assert data_point.category == "sales"
        assert data_point.metadata == {"source": "test"}
        assert data_point.is_valid is True
        assert data_point.error_message is None
        assert isinstance(data_point.timestamp, datetime)
    
    def test_data_point_with_defaults(self):
        """Test data point creation with default values."""
        data_point = DataPoint(id="test", value=10.0, category="sales")
        
        assert data_point.metadata == {}
        assert data_point.is_valid is True
        assert data_point.error_message is None
        assert (datetime.utcnow() - data_point.timestamp) < timedelta(seconds=1)
    
    @pytest.mark.parametrize("value", [-1, -100.5, -0.1])
    def test_negative_value_validation(self, value):
        """Test that negative values are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            DataPoint(id="test", value=value, category="sales")
        
        assert "Value cannot be negative" in str(exc_info.value)
    
    @pytest.mark.parametrize("value", ["not_a_number", None, [1, 2, 3]])
    def test_invalid_value_type(self, value):
        """Test that non-numeric values are rejected."""
        with pytest.raises(ValidationError):
            DataPoint(id="test", value=value, category="sales")
    
    @pytest.mark.parametrize("category", ["invalid", "SALES", "random_category"])
    def test_invalid_category_validation(self, category):
        """Test that invalid categories are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            DataPoint(id="test", value=10.0, category=category)
        
        assert "Category must be one of" in str(exc_info.value)
    
    @pytest.mark.parametrize("category", ["sales", "marketing", "operations", "finance", "other"])
    def test_valid_categories(self, category):
        """Test that all valid categories are accepted."""
        data_point = DataPoint(id="test", value=10.0, category=category)
        assert data_point.category == category
    
    def test_category_case_normalization(self):
        """Test that category is normalized to lowercase."""
        data_point = DataPoint(id="test", value=10.0, category="SALES")
        assert data_point.category == "sales"
    
    def test_to_dict_serialization(self):
        """Test dictionary serialization."""
        data_point = DataPoint(
            id="test",
            value=42.0,
            category="sales",
            metadata={"key": "value"}
        )
        
        result = data_point.to_dict()
        
        assert result["id"] == "test"
        assert result["value"] == 42.0
        assert result["category"] == "sales"
        assert result["metadata"] == {"key": "value"}
        assert result["is_valid"] is True
        assert result["error_message"] is None
        assert "timestamp" in result
    
    def test_error_data_point_creation(self):
        """Test creating error data points."""
        error_point = DataPoint.error("test-error", "sales", "Something went wrong")
        
        assert error_point.id == "test-error"
        assert error_point.category == "sales"
        assert error_point.value == 0.0
        assert error_point.is_valid is False
        assert error_point.error_message == "Something went wrong"


class TestAnalysisResult:
    """Test the AnalysisResult model."""
    
    def test_analysis_result_creation(self):
        """Test creating an analysis result."""
        result = AnalysisResult(
            total_points=100,
            valid_points=95,
            invalid_points=5,
            categories={"sales": 50, "marketing": 50},
            statistics={"mean": 42.5, "std": 10.2},
            processing_time_ms=250.5
        )
        
        assert result.total_points == 100
        assert result.valid_points == 95
        assert result.invalid_points == 5
        assert result.categories == {"sales": 50, "marketing": 50}
        assert result.statistics == {"mean": 42.5, "std": 10.2}
        assert result.processing_time_ms == 250.5
        assert isinstance(result.generated_at, datetime)
    
    def test_success_rate_calculation(self):
        """Test success rate property calculation."""
        result = AnalysisResult(
            total_points=100,
            valid_points=80,
            invalid_points=20,
            categories={},
            statistics={},
            processing_time_ms=100.0
        )
        
        assert result.success_rate == 80.0
    
    def test_success_rate_zero_division(self):
        """Test success rate when total points is zero."""
        result = AnalysisResult(
            total_points=0,
            valid_points=0,
            invalid_points=0,
            categories={},
            statistics={},
            processing_time_ms=0.0
        )
        
        assert result.success_rate == 0.0
    
    def test_summary_property(self):
        """Test the summary property."""
        result = AnalysisResult(
            total_points=50,
            valid_points=45,
            invalid_points=5,
            categories={},
            statistics={},
            processing_time_ms=123.45
        )
        
        summary = result.summary
        
        assert "50 data points" in summary
        assert "45 valid" in summary
        assert "5 invalid" in summary
        assert "123.45ms" in summary
        assert "90.0%" in summary  # Success rate


class TestProcessingConfig:
    """Test the ProcessingConfig model."""
    
    def test_default_config_creation(self):
        """Test creating config with default values."""
        config = ProcessingConfig()
        
        assert config.batch_size == 100
        assert config.parallel_workers == 4
        assert config.timeout_seconds == 30
        assert config.enable_caching is True
        assert config.cache_ttl_seconds == 3600
        assert config.validate_data is True
        assert config.retry_failed is True
        assert config.max_retries == 3
    
    def test_custom_config_creation(self):
        """Test creating config with custom values."""
        config = ProcessingConfig(
            batch_size=200,
            parallel_workers=8,
            timeout_seconds=60,
            enable_caching=False
        )
        
        assert config.batch_size == 200
        assert config.parallel_workers == 8
        assert config.timeout_seconds == 60
        assert config.enable_caching is False
    
    @pytest.mark.parametrize("batch_size", [0, -1, 10001])
    def test_batch_size_validation(self, batch_size):
        """Test batch size validation."""
        with pytest.raises(ValidationError):
            ProcessingConfig(batch_size=batch_size)
    
    @pytest.mark.parametrize("workers", [0, -1, 33])
    def test_parallel_workers_validation(self, workers):
        """Test parallel workers validation."""
        with pytest.raises(ValidationError):
            ProcessingConfig(parallel_workers=workers)
    
    def test_workers_exceed_batch_size_validation(self):
        """Test that workers cannot exceed batch size."""
        with pytest.raises(ValidationError) as exc_info:
            ProcessingConfig(batch_size=10, parallel_workers=15)
        
        assert "Workers cannot exceed batch size" in str(exc_info.value)
    
    @pytest.mark.parametrize("timeout", [0, -1, 301])
    def test_timeout_validation(self, timeout):
        """Test timeout validation."""
        with pytest.raises(ValidationError):
            ProcessingConfig(timeout_seconds=timeout)
    
    @pytest.mark.parametrize("ttl", [59, -1])
    def test_cache_ttl_validation(self, ttl):
        """Test cache TTL validation."""
        with pytest.raises(ValidationError):
            ProcessingConfig(cache_ttl_seconds=ttl)
    
    @pytest.mark.parametrize("retries", [-1, 11])
    def test_max_retries_validation(self, retries):
        """Test max retries validation."""
        with pytest.raises(ValidationError):
            ProcessingConfig(max_retries=retries)
    
    def test_valid_edge_cases(self):
        """Test valid edge case values."""
        config = ProcessingConfig(
            batch_size=1,  # Minimum
            parallel_workers=1,  # Minimum
            timeout_seconds=1,  # Minimum
            cache_ttl_seconds=60,  # Minimum
            max_retries=0  # Minimum
        )
        
        assert config.batch_size == 1
        assert config.parallel_workers == 1
        assert config.timeout_seconds == 1
        assert config.cache_ttl_seconds == 60
        assert config.max_retries == 0
        
        config_max = ProcessingConfig(
            batch_size=10000,  # Maximum
            parallel_workers=32,  # Maximum
            timeout_seconds=300,  # Maximum
            max_retries=10  # Maximum
        )
        
        assert config_max.batch_size == 10000
        assert config_max.parallel_workers == 32
        assert config_max.timeout_seconds == 300
        assert config_max.max_retries == 10
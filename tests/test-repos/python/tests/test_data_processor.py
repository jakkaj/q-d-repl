"""Unit tests for DataProcessor async functionality."""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timedelta

from src.data_processor import DataProcessor
from src.models import DataPoint, ProcessingConfig, AnalysisResult


@pytest.fixture
def sample_data_points():
    """Create sample data points for testing."""
    return [
        DataPoint(id="test-1", value=10.0, category="sales"),
        DataPoint(id="test-2", value=20.0, category="marketing"),
        DataPoint(id="test-3", value=30.0, category="operations"),
        DataPoint(id="test-4", value=40.0, category="finance"),
        DataPoint(id="test-5", value=50.0, category="sales"),
    ]


@pytest.fixture
def test_config():
    """Create test configuration."""
    return ProcessingConfig(
        batch_size=2,
        parallel_workers=2,
        timeout_seconds=10,
        enable_caching=True,
        cache_ttl_seconds=60
    )


class TestDataProcessor:
    """Test the DataProcessor async functionality."""
    
    @pytest.mark.asyncio
    async def test_context_manager(self, test_config):
        """Test that DataProcessor works as async context manager."""
        async with DataProcessor(test_config) as processor:
            assert processor is not None
            assert processor.config == test_config
            assert processor._semaphore._value == test_config.parallel_workers
    
    @pytest.mark.asyncio
    async def test_process_data_points_basic(self, test_config, sample_data_points):
        """Test basic data processing functionality."""
        async with DataProcessor(test_config) as processor:
            result = await processor.process_data_points(sample_data_points)
            
            assert isinstance(result, AnalysisResult)
            assert result.total_points == len(sample_data_points)
            assert result.valid_points == len(sample_data_points)
            assert result.invalid_points == 0
            assert result.processing_time_ms > 0
            
            # Check categories
            expected_categories = {"sales": 2, "marketing": 1, "operations": 1, "finance": 1}
            assert result.categories == expected_categories
            
            # Check basic statistics
            assert "mean" in result.statistics
            assert "count" in result.statistics
            assert result.statistics["count"] == len(sample_data_points)
    
    @pytest.mark.asyncio
    async def test_process_empty_list(self, test_config):
        """Test processing empty data point list."""
        async with DataProcessor(test_config) as processor:
            result = await processor.process_data_points([])
            
            assert result.total_points == 0
            assert result.valid_points == 0
            assert result.invalid_points == 0
            assert result.categories == {}
            assert result.statistics == {}
    
    @pytest.mark.asyncio
    async def test_process_error_data_points(self, test_config):
        """Test processing data points with errors."""
        data_points = [
            DataPoint(id="valid", value=10.0, category="sales"),
            DataPoint.error("error-1", "sales", "Test error"),
            DataPoint.error("error-2", "marketing", "Another error")
        ]
        
        async with DataProcessor(test_config) as processor:
            result = await processor.process_data_points(data_points)
            
            assert result.total_points == 3
            assert result.valid_points == 1
            assert result.invalid_points == 2
            assert result.categories == {"sales": 2, "marketing": 1}
    
    @pytest.mark.asyncio
    async def test_batch_processing(self, test_config, sample_data_points):
        """Test that data is processed in batches."""
        # Use small batch size to force multiple batches
        config = ProcessingConfig(batch_size=2, parallel_workers=1)
        
        async with DataProcessor(config) as processor:
            with patch.object(processor, '_process_batch', new_callable=AsyncMock) as mock_batch:
                mock_batch.return_value = sample_data_points[:2]  # Return partial data
                
                # This should create 3 batches for 5 data points with batch_size=2
                await processor.process_data_points(sample_data_points)
                
                # Should be called 3 times: [2, 2, 1] items per batch
                assert mock_batch.call_count == 3
    
    @pytest.mark.asyncio
    async def test_enrichment_caching(self, test_config):
        """Test that enrichment data is cached correctly."""
        data_points = [
            DataPoint(id="test-1", value=10.0, category="sales"),
            DataPoint(id="test-2", value=20.0, category="sales"),  # Same category
        ]
        
        async with DataProcessor(test_config) as processor:
            with patch.object(processor, '_fetch_enrichment_data', new_callable=AsyncMock) as mock_fetch:
                mock_fetch.return_value = {"region": "North"}
                
                await processor.process_data_points(data_points)
                
                # Should only fetch once due to caching
                assert mock_fetch.call_count == 1
                mock_fetch.assert_called_with("sales")
    
    @pytest.mark.asyncio
    async def test_cache_expiration(self, test_config):
        """Test that cache expires correctly."""
        # Use very short cache TTL
        config = ProcessingConfig(
            batch_size=10,
            parallel_workers=1,
            enable_caching=True,
            cache_ttl_seconds=1  # 1 second TTL
        )
        
        data_point = DataPoint(id="test", value=10.0, category="sales")
        
        async with DataProcessor(config) as processor:
            with patch.object(processor, '_fetch_enrichment_data', new_callable=AsyncMock) as mock_fetch:
                mock_fetch.return_value = {"region": "North"}
                
                # First call - should fetch
                await processor.process_data_points([data_point])
                assert mock_fetch.call_count == 1
                
                # Second call immediately - should use cache
                await processor.process_data_points([data_point])
                assert mock_fetch.call_count == 1
                
                # Wait for cache to expire and call again
                await asyncio.sleep(1.1)
                await processor.process_data_points([data_point])
                assert mock_fetch.call_count == 2
    
    @pytest.mark.asyncio
    async def test_caching_disabled(self, test_config):
        """Test behavior when caching is disabled."""
        config = ProcessingConfig(
            batch_size=10,
            parallel_workers=1,
            enable_caching=False
        )
        
        data_points = [
            DataPoint(id="test-1", value=10.0, category="sales"),
            DataPoint(id="test-2", value=20.0, category="sales"),  # Same category
        ]
        
        async with DataProcessor(config) as processor:
            with patch.object(processor, '_fetch_enrichment_data', new_callable=AsyncMock) as mock_fetch:
                mock_fetch.return_value = {"region": "North"}
                
                await processor.process_data_points(data_points)
                
                # Should fetch twice since caching is disabled
                assert mock_fetch.call_count == 2
    
    @pytest.mark.asyncio
    async def test_concurrent_processing(self, test_config, sample_data_points):
        """Test concurrent processing with semaphore."""
        config = ProcessingConfig(batch_size=1, parallel_workers=2)  # Force individual processing
        
        async with DataProcessor(config) as processor:
            # Mock _process_batch to track concurrent calls
            original_process_batch = processor._process_batch
            call_times = []
            
            async def tracked_process_batch(batch):
                call_times.append(asyncio.get_event_loop().time())
                await asyncio.sleep(0.1)  # Simulate processing time
                return await original_process_batch(batch)
            
            processor._process_batch = tracked_process_batch
            
            start_time = asyncio.get_event_loop().time()
            await processor.process_data_points(sample_data_points)
            total_time = asyncio.get_event_loop().time() - start_time
            
            # With parallel processing, should take less time than sequential
            # Sequential would be ~0.5s (5 * 0.1s), parallel should be ~0.3s
            assert total_time < 0.4  # Allow some margin
            assert len(call_times) == len(sample_data_points)
    
    @pytest.mark.asyncio
    async def test_statistics_calculation(self, test_config):
        """Test statistics calculation with known data."""
        data_points = [
            DataPoint(id="test-1", value=10.0, category="sales"),
            DataPoint(id="test-2", value=20.0, category="sales"),
            DataPoint(id="test-3", value=30.0, category="marketing"),
        ]
        
        async with DataProcessor(test_config) as processor:
            result = await processor.process_data_points(data_points)
            
            stats = result.statistics
            
            # Check basic statistics
            assert stats["mean"] == 20.0  # (10 + 20 + 30) / 3
            assert stats["min"] == 10.0
            assert stats["max"] == 30.0
            assert stats["sum"] == 60.0
            assert stats["count"] == 3
            
            # Check category-specific statistics
            assert stats["sales_mean"] == 15.0  # (10 + 20) / 2
            assert stats["sales_count"] == 2
            assert stats["marketing_mean"] == 30.0
            assert stats["marketing_count"] == 1
    
    @pytest.mark.asyncio
    async def test_stream_processing(self, test_config):
        """Test streaming data processing."""
        async def data_stream():
            for i in range(10):
                yield DataPoint(id=f"stream-{i}", value=float(i), category="sales")
        
        config = ProcessingConfig(batch_size=3, parallel_workers=1)
        
        async with DataProcessor(config) as processor:
            results = []
            async for result in processor.stream_process_data(data_stream()):
                results.append(result)
            
            # Should have multiple results due to batching
            assert len(results) >= 2  # At least 2 batches for 10 items with batch_size=3
            
            # Sum up all processed points
            total_processed = sum(r.total_points for r in results)
            assert total_processed == 10
    
    @pytest.mark.asyncio
    async def test_health_check(self, test_config):
        """Test health check functionality."""
        async with DataProcessor(test_config) as processor:
            health = await processor.health_check()
            
            assert health["status"] == "healthy"
            assert "processing_time_ms" in health
            assert "cache_size" in health
            assert "workers" in health
            assert "test_result" in health
            assert health["workers"] == test_config.parallel_workers
    
    @pytest.mark.asyncio
    async def test_health_check_with_error(self, test_config):
        """Test health check when processing fails."""
        async with DataProcessor(test_config) as processor:
            # Mock process_data_points to raise an exception
            with patch.object(processor, 'process_data_points', new_callable=AsyncMock) as mock_process:
                mock_process.side_effect = Exception("Processing failed")
                
                health = await processor.health_check()
                
                assert health["status"] == "unhealthy"
                assert "error" in health
                assert "Processing failed" in health["error"]
    
    @pytest.mark.asyncio
    async def test_enrichment_data_generation(self, test_config):
        """Test enrichment data generation for different categories."""
        async with DataProcessor(test_config) as processor:
            # Test different categories
            sales_data = await processor._fetch_enrichment_data("sales")
            marketing_data = await processor._fetch_enrichment_data("marketing")
            operations_data = await processor._fetch_enrichment_data("operations")
            finance_data = await processor._fetch_enrichment_data("finance")
            other_data = await processor._fetch_enrichment_data("unknown")
            
            # Each category should have different enrichment data
            assert sales_data != marketing_data
            assert sales_data["region"] == "North"
            assert marketing_data["channel"] == "Digital"
            assert operations_data["facility"] == "Warehouse-A"
            assert finance_data["department"] == "Accounting"
            assert other_data["type"] == "Miscellaneous"
    
    @pytest.mark.asyncio
    async def test_batch_creation(self, test_config, sample_data_points):
        """Test batch creation logic."""
        async with DataProcessor(test_config) as processor:
            # Test with batch size that divides evenly
            batches = processor._create_batches(sample_data_points, 2)
            assert len(batches) == 3  # 5 items, batch size 2: [2, 2, 1]
            assert len(batches[0]) == 2
            assert len(batches[1]) == 2
            assert len(batches[2]) == 1
            
            # Test with batch size larger than data
            large_batches = processor._create_batches(sample_data_points, 10)
            assert len(large_batches) == 1
            assert len(large_batches[0]) == 5
            
            # Test with batch size of 1
            single_batches = processor._create_batches(sample_data_points, 1)
            assert len(single_batches) == 5
            assert all(len(batch) == 1 for batch in single_batches)
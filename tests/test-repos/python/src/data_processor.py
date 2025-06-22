"""Advanced async data processing service."""

import asyncio
import aiohttp
import time
import json
from typing import List, Dict, Any, Optional, AsyncGenerator
from datetime import datetime, timedelta
import logging
from concurrent.futures import ThreadPoolExecutor
import pandas as pd
import numpy as np

from .models import DataPoint, AnalysisResult, ProcessingConfig


logger = logging.getLogger(__name__)


class DataProcessor:
    """Advanced data processor with async operations, caching, and parallel processing."""
    
    def __init__(self, config: ProcessingConfig):
        self.config = config
        self._cache: Dict[str, Any] = {}
        self._cache_timestamps: Dict[str, datetime] = {}
        self._semaphore = asyncio.Semaphore(config.parallel_workers)
        self._session: Optional[aiohttp.ClientSession] = None
        self._executor = ThreadPoolExecutor(max_workers=config.parallel_workers)
    
    async def __aenter__(self):
        """Async context manager entry."""
        self._session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.config.timeout_seconds)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._session:
            await self._session.close()
        self._executor.shutdown(wait=True)
    
    async def process_data_points(self, data_points: List[DataPoint]) -> AnalysisResult:
        """Process a collection of data points with async operations."""
        start_time = time.time()
        
        logger.info(f"Processing {len(data_points)} data points with {self.config.parallel_workers} workers")
        
        # Process in batches
        batches = self._create_batches(data_points, self.config.batch_size)
        processed_batches = []
        
        # Process batches concurrently
        tasks = [self._process_batch(batch) for batch in batches]
        batch_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Collect results
        all_processed = []
        for result in batch_results:
            if isinstance(result, Exception):
                logger.error(f"Batch processing failed: {result}")
                continue
            all_processed.extend(result)
        
        # Generate analysis
        analysis = await self._generate_analysis(all_processed)
        analysis.processing_time_ms = (time.time() - start_time) * 1000
        
        logger.info(f"Processing complete: {analysis.summary}")
        return analysis
    
    async def _process_batch(self, batch: List[DataPoint]) -> List[DataPoint]:
        """Process a single batch of data points."""
        async with self._semaphore:
            processed = []
            
            for data_point in batch:
                try:
                    # Simulate some async processing
                    await asyncio.sleep(0.01)  # Simulate I/O delay
                    
                    # Validate and enrich data point
                    enriched = await self._enrich_data_point(data_point)
                    processed.append(enriched)
                    
                except Exception as e:
                    logger.warning(f"Failed to process data point {data_point.id}: {e}")
                    error_point = DataPoint.error(
                        data_point.id, 
                        data_point.category, 
                        str(e)
                    )
                    processed.append(error_point)
            
            return processed
    
    async def _enrich_data_point(self, data_point: DataPoint) -> DataPoint:
        """Enrich a data point with additional metadata."""
        # Simulate external API call for enrichment
        if self.config.enable_caching:
            cached_data = self._get_cached_enrichment(data_point.category)
            if cached_data:
                data_point.metadata.update(cached_data)
                return data_point
        
        # Simulate async enrichment process
        enrichment_data = await self._fetch_enrichment_data(data_point.category)
        
        if self.config.enable_caching:
            self._cache_enrichment_data(data_point.category, enrichment_data)
        
        data_point.metadata.update(enrichment_data)
        return data_point
    
    async def _fetch_enrichment_data(self, category: str) -> Dict[str, Any]:
        """Fetch enrichment data (simulated external API call)."""
        await asyncio.sleep(0.005)  # Simulate API latency
        
        # Simulate different enrichment data based on category
        enrichment_map = {
            'sales': {'region': 'North', 'quarter': 'Q4', 'team_size': 12},
            'marketing': {'channel': 'Digital', 'campaign': 'Holiday2023', 'budget': 50000},
            'operations': {'facility': 'Warehouse-A', 'shift': 'Day', 'capacity': 1000},
            'finance': {'department': 'Accounting', 'fiscal_year': 2023, 'currency': 'USD'},
            'other': {'type': 'Miscellaneous', 'priority': 'Low'}
        }
        
        return enrichment_map.get(category, enrichment_map['other'])
    
    def _get_cached_enrichment(self, category: str) -> Optional[Dict[str, Any]]:
        """Get cached enrichment data if still valid."""
        if not self.config.enable_caching:
            return None
        
        cache_key = f"enrichment_{category}"
        if cache_key not in self._cache:
            return None
        
        # Check if cache is still valid
        cached_time = self._cache_timestamps.get(cache_key)
        if not cached_time:
            return None
        
        if datetime.utcnow() - cached_time > timedelta(seconds=self.config.cache_ttl_seconds):
            # Cache expired
            del self._cache[cache_key]
            del self._cache_timestamps[cache_key]
            return None
        
        return self._cache[cache_key]
    
    def _cache_enrichment_data(self, category: str, data: Dict[str, Any]):
        """Cache enrichment data."""
        if not self.config.enable_caching:
            return
        
        cache_key = f"enrichment_{category}"
        self._cache[cache_key] = data.copy()
        self._cache_timestamps[cache_key] = datetime.utcnow()
    
    async def _generate_analysis(self, data_points: List[DataPoint]) -> AnalysisResult:
        """Generate comprehensive analysis of processed data points."""
        valid_points = [dp for dp in data_points if dp.is_valid]
        invalid_points = [dp for dp in data_points if not dp.is_valid]
        
        # Category distribution
        categories = {}
        for dp in data_points:
            categories[dp.category] = categories.get(dp.category, 0) + 1
        
        # Statistical analysis using pandas (CPU-intensive, run in thread pool)
        statistics = await asyncio.get_event_loop().run_in_executor(
            self._executor,
            self._calculate_statistics,
            valid_points
        )
        
        return AnalysisResult(
            total_points=len(data_points),
            valid_points=len(valid_points),
            invalid_points=len(invalid_points),
            categories=categories,
            statistics=statistics,
            processing_time_ms=0.0  # Will be set by caller
        )
    
    def _calculate_statistics(self, valid_points: List[DataPoint]) -> Dict[str, float]:
        """Calculate statistics using pandas (CPU-intensive operation)."""
        if not valid_points:
            return {}
        
        # Convert to pandas DataFrame for analysis
        df_data = []
        for dp in valid_points:
            df_data.append({
                'value': dp.value,
                'category': dp.category,
                'timestamp': dp.timestamp
            })
        
        df = pd.DataFrame(df_data)
        
        # Calculate comprehensive statistics
        stats = {
            'mean': float(df['value'].mean()),
            'median': float(df['value'].median()),
            'std_dev': float(df['value'].std()),
            'min': float(df['value'].min()),
            'max': float(df['value'].max()),
            'sum': float(df['value'].sum()),
            'count': len(df),
        }
        
        # Category-specific statistics
        for category in df['category'].unique():
            cat_data = df[df['category'] == category]['value']
            stats[f'{category}_mean'] = float(cat_data.mean())
            stats[f'{category}_count'] = len(cat_data)
        
        return stats
    
    def _create_batches(self, items: List[DataPoint], batch_size: int) -> List[List[DataPoint]]:
        """Split items into batches of specified size."""
        batches = []
        for i in range(0, len(items), batch_size):
            batches.append(items[i:i + batch_size])
        return batches
    
    async def stream_process_data(self, data_stream: AsyncGenerator[DataPoint, None]) -> AsyncGenerator[AnalysisResult, None]:
        """Process streaming data points and yield incremental results."""
        batch = []
        async for data_point in data_stream:
            batch.append(data_point)
            
            if len(batch) >= self.config.batch_size:
                result = await self.process_data_points(batch)
                yield result
                batch = []
        
        # Process remaining items
        if batch:
            result = await self.process_data_points(batch)
            yield result
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform a health check of the data processor."""
        start_time = time.time()
        
        # Test data processing with sample data
        test_data = [
            DataPoint(id="health-1", value=100.0, category="sales"),
            DataPoint(id="health-2", value=200.0, category="marketing")
        ]
        
        try:
            result = await self.process_data_points(test_data)
            processing_time = (time.time() - start_time) * 1000
            
            return {
                'status': 'healthy',
                'processing_time_ms': processing_time,
                'cache_size': len(self._cache),
                'workers': self.config.parallel_workers,
                'test_result': result.summary
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'processing_time_ms': (time.time() - start_time) * 1000
            }
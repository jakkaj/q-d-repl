#!/usr/bin/env python3
"""
Main application demonstrating async data processing and web service.
"""

import asyncio
import logging
import sys
from datetime import datetime
from typing import List
import json

from src.models import DataPoint, ProcessingConfig
from src.data_processor import DataProcessor
from src.web_service import DataAnalysisService


async def demo_data_processing():
    """Demonstrate advanced data processing capabilities."""
    print("=== Data Processing Demo ===")
    
    # Create configuration
    config = ProcessingConfig(
        batch_size=25,
        parallel_workers=3,
        enable_caching=True,
        validate_data=True
    )
    
    # Generate sample data
    data_points = []
    categories = ['sales', 'marketing', 'operations', 'finance']
    
    for i in range(100):
        data_point = DataPoint(
            id=f'dp-{i:03d}',
            value=float(i * 2.5 + 10),
            category=categories[i % len(categories)],
            metadata={'source': 'demo', 'batch': i // 25}
        )
        data_points.append(data_point)
    
    # Add some invalid data points for error handling demo
    data_points.append(DataPoint.error('error-1', 'sales', 'Simulated error'))
    
    print(f"Generated {len(data_points)} data points for processing")
    
    # Process data
    async with DataProcessor(config) as processor:
        print("Starting data processing...")
        
        result = await processor.process_data_points(data_points)
        
        print(f"\nProcessing Results:")
        print(f"  {result.summary}")
        print(f"  Categories: {result.categories}")
        print(f"  Key Statistics:")
        for key, value in result.statistics.items():
            if isinstance(value, float):
                print(f"    {key}: {value:.2f}")
            else:
                print(f"    {key}: {value}")
        
        # Demonstrate health check
        health = await processor.health_check()
        print(f"\nHealth Check: {health['status']}")
        print(f"Cache size: {health.get('cache_size', 0)} items")


async def demo_streaming_processing():
    """Demonstrate streaming data processing."""
    print("\n=== Streaming Processing Demo ===")
    
    async def generate_stream():
        """Generate a stream of data points."""
        for i in range(50):
            await asyncio.sleep(0.01)  # Simulate real-time data
            yield DataPoint(
                id=f'stream-{i}',
                value=float(i * 1.5),
                category=['sales', 'operations'][i % 2]
            )
    
    config = ProcessingConfig(batch_size=10, parallel_workers=2)
    
    async with DataProcessor(config) as processor:
        print("Processing streaming data...")
        
        batch_count = 0
        async for result in processor.stream_process_data(generate_stream()):
            batch_count += 1
            print(f"  Batch {batch_count}: {result.summary}")


async def demo_concurrent_processing():
    """Demonstrate concurrent processing of multiple datasets."""
    print("\n=== Concurrent Processing Demo ===")
    
    config = ProcessingConfig(parallel_workers=4, batch_size=20)
    
    # Create multiple datasets
    datasets = []
    for dataset_id in range(3):
        dataset = []
        for i in range(30):
            dataset.append(DataPoint(
                id=f'ds{dataset_id}-{i}',
                value=float(i + dataset_id * 100),
                category=['sales', 'marketing', 'finance'][dataset_id]
            ))
        datasets.append(dataset)
    
    # Process all datasets concurrently
    async with DataProcessor(config) as processor:
        print("Processing multiple datasets concurrently...")
        
        tasks = [
            processor.process_data_points(dataset) 
            for dataset in datasets
        ]
        
        results = await asyncio.gather(*tasks)
        
        print(f"Processed {len(datasets)} datasets:")
        for i, result in enumerate(results):
            print(f"  Dataset {i}: {result.summary}")


async def demo_web_service():
    """Demonstrate the web service (non-blocking start)."""
    print("\n=== Web Service Demo ===")
    
    config = ProcessingConfig(
        batch_size=20,
        parallel_workers=2,
        enable_caching=True
    )
    
    service = DataAnalysisService(config)
    await service.start_processor()
    
    # Demonstrate health check
    try:
        # Simulate a request by calling the processor directly
        health = await service._processor.health_check()
        print(f"Web service health: {health['status']}")
        print(f"Service would be available at: http://127.0.0.1:8080")
        print("API endpoints:")
        print("  GET  /health - Service health check")
        print("  POST /analyze - Analyze single data point")
        print("  POST /analyze/batch - Analyze multiple data points")
        print("  GET  /config - Get configuration")
        print("  PUT  /config - Update configuration")
        print("  GET  /stats - Get statistics")
        
    finally:
        await service.stop_processor()


async def run_performance_test():
    """Run a performance test with larger datasets."""
    print("\n=== Performance Test ===")
    
    config = ProcessingConfig(
        batch_size=100,
        parallel_workers=8,
        enable_caching=True,
        timeout_seconds=60
    )
    
    # Generate large dataset
    large_dataset = []
    for i in range(1000):
        large_dataset.append(DataPoint(
            id=f'perf-{i:04d}',
            value=float(i * 0.5 + 1),
            category=['sales', 'marketing', 'operations', 'finance'][i % 4],
            metadata={'performance_test': True, 'index': i}
        ))
    
    print(f"Performance testing with {len(large_dataset)} data points...")
    
    async with DataProcessor(config) as processor:
        start_time = asyncio.get_event_loop().time()
        
        result = await processor.process_data_points(large_dataset)
        
        end_time = asyncio.get_event_loop().time()
        total_time = end_time - start_time
        
        print(f"Performance Results:")
        print(f"  Total processing time: {total_time:.2f} seconds")
        print(f"  Processing rate: {len(large_dataset) / total_time:.0f} points/second")
        print(f"  {result.summary}")


async def main():
    """Run all demonstrations."""
    print("Advanced Python Data Processing and Web Service Demo")
    print("=" * 60)
    
    try:
        await demo_data_processing()
        await demo_streaming_processing()
        await demo_concurrent_processing()
        await demo_web_service()
        await run_performance_test()
        
        print("\n" + "=" * 60)
        print("✅ All demonstrations completed successfully!")
        print("This application showcases:")
        print("  • Async/await programming patterns")
        print("  • Concurrent and parallel processing")
        print("  • Pydantic data validation")
        print("  • Error handling and resilience")
        print("  • Caching and performance optimization")
        print("  • RESTful web service with aiohttp")
        print("  • Data analysis with pandas/numpy")
        print("  • Streaming data processing")
        print("  • Health monitoring and statistics")
        
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        logging.exception("Demo error")
        sys.exit(1)


if __name__ == '__main__':
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run the main demo
    asyncio.run(main())
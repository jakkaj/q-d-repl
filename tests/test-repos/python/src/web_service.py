"""Async web service using aiohttp for data analysis API."""

import asyncio
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from aiohttp import web, ClientSession
import aiohttp_cors

from .models import DataPoint, ProcessingConfig
from .data_processor import DataProcessor


logger = logging.getLogger(__name__)


class DataAnalysisService:
    """RESTful web service for data analysis operations."""
    
    def __init__(self, config: ProcessingConfig):
        self.config = config
        self.app = web.Application()
        self._setup_routes()
        self._setup_cors()
        self._processor: Optional[DataProcessor] = None
    
    def _setup_routes(self):
        """Set up HTTP routes."""
        self.app.router.add_get('/', self.health_check)
        self.app.router.add_get('/health', self.health_check)
        self.app.router.add_post('/analyze', self.analyze_data)
        self.app.router.add_post('/analyze/batch', self.analyze_batch)
        self.app.router.add_get('/config', self.get_config)
        self.app.router.add_put('/config', self.update_config)
        self.app.router.add_get('/stats', self.get_statistics)
    
    def _setup_cors(self):
        """Set up CORS for cross-origin requests."""
        cors = aiohttp_cors.setup(self.app, defaults={
            "*": aiohttp_cors.ResourceOptions(
                allow_credentials=True,
                expose_headers="*",
                allow_headers="*",
                allow_methods="*"
            )
        })
        
        # Add CORS to all routes
        for route in list(self.app.router.routes()):
            cors.add(route)
    
    async def start_processor(self):
        """Start the data processor."""
        self._processor = DataProcessor(self.config)
        await self._processor.__aenter__()
    
    async def stop_processor(self):
        """Stop the data processor."""
        if self._processor:
            await self._processor.__aexit__(None, None, None)
    
    async def health_check(self, request: web.Request) -> web.Response:
        """Health check endpoint."""
        try:
            if not self._processor:
                await self.start_processor()
            
            health_data = await self._processor.health_check()
            health_data['service'] = 'DataAnalysisService'
            health_data['timestamp'] = datetime.utcnow().isoformat()
            health_data['version'] = '1.0.0'
            
            return web.json_response(health_data)
        
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return web.json_response(
                {'status': 'unhealthy', 'error': str(e)},
                status=503
            )
    
    async def analyze_data(self, request: web.Request) -> web.Response:
        """Analyze a single data point."""
        try:
            data = await request.json()
            
            # Validate input
            if 'id' not in data or 'value' not in data or 'category' not in data:
                return web.json_response(
                    {'error': 'Missing required fields: id, value, category'},
                    status=400
                )
            
            # Create data point
            data_point = DataPoint(
                id=data['id'],
                value=float(data['value']),
                category=data['category'],
                metadata=data.get('metadata', {})
            )
            
            # Process data
            if not self._processor:
                await self.start_processor()
            
            result = await self._processor.process_data_points([data_point])
            
            return web.json_response({
                'success': True,
                'data_point': data_point.to_dict(),
                'analysis': result.dict()
            })
        
        except ValueError as e:
            return web.json_response({'error': f'Validation error: {e}'}, status=400)
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            return web.json_response({'error': str(e)}, status=500)
    
    async def analyze_batch(self, request: web.Request) -> web.Response:
        """Analyze a batch of data points."""
        try:
            data = await request.json()
            
            if 'data_points' not in data:
                return web.json_response(
                    {'error': 'Missing data_points array'},
                    status=400
                )
            
            # Create data points
            data_points = []
            for i, point_data in enumerate(data['data_points']):
                try:
                    data_point = DataPoint(
                        id=point_data.get('id', f'batch-{i}'),
                        value=float(point_data['value']),
                        category=point_data['category'],
                        metadata=point_data.get('metadata', {})
                    )
                    data_points.append(data_point)
                except Exception as e:
                    # Create error data point for invalid data
                    error_point = DataPoint.error(
                        f'batch-{i}',
                        point_data.get('category', 'unknown'),
                        str(e)
                    )
                    data_points.append(error_point)
            
            # Process batch
            if not self._processor:
                await self.start_processor()
            
            result = await self._processor.process_data_points(data_points)
            
            return web.json_response({
                'success': True,
                'processed_count': len(data_points),
                'analysis': result.dict()
            })
        
        except Exception as e:
            logger.error(f"Batch analysis failed: {e}")
            return web.json_response({'error': str(e)}, status=500)
    
    async def get_config(self, request: web.Request) -> web.Response:
        """Get current processing configuration."""
        return web.json_response(self.config.dict())
    
    async def update_config(self, request: web.Request) -> web.Response:
        """Update processing configuration."""
        try:
            data = await request.json()
            
            # Update configuration
            new_config = ProcessingConfig(**{**self.config.dict(), **data})
            self.config = new_config
            
            # Restart processor with new config
            if self._processor:
                await self.stop_processor()
            await self.start_processor()
            
            return web.json_response({
                'success': True,
                'config': self.config.dict()
            })
        
        except Exception as e:
            logger.error(f"Config update failed: {e}")
            return web.json_response({'error': str(e)}, status=400)
    
    async def get_statistics(self, request: web.Request) -> web.Response:
        """Get service statistics."""
        try:
            # Generate some sample data for statistics
            sample_data = []
            for i in range(100):
                sample_data.append(DataPoint(
                    id=f'sample-{i}',
                    value=float(i * 1.5 + 10),
                    category=['sales', 'marketing', 'operations'][i % 3]
                ))
            
            if not self._processor:
                await self.start_processor()
            
            result = await self._processor.process_data_points(sample_data)
            
            return web.json_response({
                'success': True,
                'sample_analysis': result.dict(),
                'service_stats': {
                    'config': self.config.dict(),
                    'timestamp': datetime.utcnow().isoformat()
                }
            })
        
        except Exception as e:
            logger.error(f"Statistics generation failed: {e}")
            return web.json_response({'error': str(e)}, status=500)
    
    async def run_server(self, host: str = '127.0.0.1', port: int = 8080):
        """Run the web server."""
        await self.start_processor()
        
        runner = web.AppRunner(self.app)
        await runner.setup()
        
        site = web.TCPSite(runner, host, port)
        await site.start()
        
        logger.info(f"Data Analysis Service running on http://{host}:{port}")
        
        try:
            # Keep the server running
            await asyncio.Future()  # Run forever
        finally:
            await self.stop_processor()
            await runner.cleanup()


async def create_app(config: ProcessingConfig) -> web.Application:
    """Create and configure the web application."""
    service = DataAnalysisService(config)
    await service.start_processor()
    return service.app


if __name__ == '__main__':
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create default configuration
    config = ProcessingConfig(
        batch_size=50,
        parallel_workers=4,
        timeout_seconds=30,
        enable_caching=True
    )
    
    # Run the service
    service = DataAnalysisService(config)
    asyncio.run(service.run_server())
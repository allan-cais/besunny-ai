"""
API Gateway for microservice architecture.
Handles routing, load balancing, and service discovery.
"""

from typing import Dict, List, Optional, Any, Callable
from fastapi import Request, HTTPException, Depends
from fastapi.responses import JSONResponse, RedirectResponse
import httpx
import logging
import json
import asyncio
from datetime import datetime

from .service_registry import ServiceRegistry, ServiceType, get_service_registry
from .config import get_settings

logger = logging.getLogger(__name__)


class APIGateway:
    """API Gateway for routing requests to microservices."""
    
    def __init__(self, service_registry: ServiceRegistry):
        self.service_registry = service_registry
        self.settings = get_settings()
        self.routing_rules: Dict[str, Dict[str, Any]] = {}
        self.rate_limiters: Dict[str, Any] = {}
        self.cache: Dict[str, Any] = {}
        self._setup_routing_rules()
    
    def _setup_routing_rules(self):
        """Setup default routing rules."""
        self.routing_rules = {
            # Document processing routes
            "/api/v1/documents": {
                "service_type": ServiceType.DOCUMENT_PROCESSING,
                "methods": ["GET", "POST", "PUT", "DELETE"],
                "cache_ttl": 300,  # 5 minutes
                "rate_limit": 100  # requests per hour
            },
            "/api/v1/documents/classify": {
                "service_type": ServiceType.AI_CLASSIFICATION,
                "methods": ["POST"],
                "cache_ttl": 0,  # No cache for classification
                "rate_limit": 50  # requests per hour
            },
            
            # AI services routes
            "/api/v1/ai": {
                "service_type": ServiceType.AI_CLASSIFICATION,
                "methods": ["GET", "POST"],
                "cache_ttl": 600,  # 10 minutes
                "rate_limit": 200  # requests per hour
            },
            "/api/v1/embeddings": {
                "service_type": ServiceType.AI_CLASSIFICATION,
                "methods": ["GET", "POST"],
                "cache_ttl": 1800,  # 30 minutes
                "rate_limit": 100  # requests per hour
            },
            "/api/v1/classification": {
                "service_type": ServiceType.AI_CLASSIFICATION,
                "methods": ["GET", "POST"],
                "cache_ttl": 0,  # No cache for classification
                "rate_limit": 100  # requests per hour
            },
            
            # Email processing routes
            "/api/v1/emails": {
                "service_type": ServiceType.EMAIL_PROCESSING,
                "methods": ["GET", "POST"],
                "cache_ttl": 300,  # 5 minutes
                "rate_limit": 200  # requests per hour
            },
            
            # Drive monitoring routes
            "/api/v1/drive": {
                "service_type": ServiceType.DRIVE_MONITORING,
                "methods": ["GET", "POST"],
                "cache_ttl": 300,  # 5 minutes
                "rate_limit": 150  # requests per hour
            },
            
            # Calendar sync routes
            "/api/v1/calendar": {
                "service_type": ServiceType.CALENDAR_SYNC,
                "methods": ["GET", "POST", "PUT", "DELETE"],
                "cache_ttl": 300,  # 5 minutes
                "rate_limit": 200  # requests per hour
            },
            
            # Meeting intelligence routes
            "/api/v1/meeting-intelligence": {
                "service_type": ServiceType.AI_CLASSIFICATION,
                "methods": ["GET", "POST"],
                "cache_ttl": 600,  # 10 minutes
                "rate_limit": 100  # requests per hour
            },
            
            # Attendee bot routes
            "/api/v1/attendee": {
                "service_type": ServiceType.ATTENDEE_BOT,
                "methods": ["GET", "POST"],
                "cache_ttl": 300,  # 5 minutes
                "rate_limit": 150  # requests per hour
            },
            
            # Projects routes
            "/api/v1/projects": {
                "service_type": ServiceType.DOCUMENT_PROCESSING,
                "methods": ["GET", "POST", "PUT", "DELETE"],
                "cache_ttl": 600,  # 10 minutes
                "rate_limit": 100  # requests per hour
            }
        }
    
    def get_routing_rule(self, path: str) -> Optional[Dict[str, Any]]:
        """Get routing rule for a specific path."""
        # Find the best matching route
        for route_pattern, rule in self.routing_rules.items():
            if path.startswith(route_pattern):
                return rule
        return None
    
    async def route_request(self, request: Request) -> JSONResponse:
        """Route the request to the appropriate microservice."""
        path = request.url.path
        method = request.method
        
        # Get routing rule
        routing_rule = self.get_routing_rule(path)
        if not routing_rule:
            raise HTTPException(status_code=404, detail="Route not found")
        
        # Check if method is allowed
        if method not in routing_rule["methods"]:
            raise HTTPException(status_code=405, detail="Method not allowed")
        
        # Check rate limiting
        if not await self._check_rate_limit(request, routing_rule):
            raise HTTPException(status_code=429, detail="Rate limit exceeded")
        
        # Check cache for GET requests
        if method == "GET" and routing_rule["cache_ttl"] > 0:
            cached_response = await self._get_cached_response(request)
            if cached_response:
                return cached_response
        
        # Route to microservice
        try:
            response = await self._forward_request(request, routing_rule)
            
            # Cache response for GET requests
            if method == "GET" and routing_rule["cache_ttl"] > 0:
                await self._cache_response(request, response, routing_rule["cache_ttl"])
            
            return response
            
        except Exception as e:
            logger.error(f"Request routing failed: {e}")
            raise HTTPException(status_code=503, detail="Service temporarily unavailable")
    
    async def _forward_request(self, request: Request, routing_rule: Dict[str, Any]) -> JSONResponse:
        """Forward request to the appropriate microservice."""
        service_type = routing_rule["service_type"]
        
        # Get healthy service for load balancing
        service = self.service_registry.select_service_for_load_balancing(service_type)
        if not service:
            raise HTTPException(status_code=503, detail="No healthy services available")
        
        # Prepare request data
        body = None
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.body()
            except Exception:
                body = None
        
        # Build target URL
        target_url = f"http://{service.host}:{service.port}{request.url.path}"
        if request.url.query:
            target_url += f"?{request.url.query}"
        
        # Forward headers (filter out some headers)
        headers = dict(request.headers)
        headers_to_remove = ["host", "content-length", "transfer-encoding"]
        for header in headers_to_remove:
            headers.pop(header, None)
        
        # Make request to microservice
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.request(
                    method=request.method,
                    url=target_url,
                    headers=headers,
                    content=body,
                    params=request.query_params
                )
                
                # Convert response to JSONResponse
                return JSONResponse(
                    content=response.json() if response.content else {},
                    status_code=response.status_code,
                    headers=dict(response.headers)
                )
                
            except httpx.TimeoutException:
                logger.error(f"Request timeout to {service.service_id}")
                raise HTTPException(status_code=504, detail="Gateway timeout")
            except httpx.RequestError as e:
                logger.error(f"Request error to {service.service_id}: {e}")
                raise HTTPException(status_code=503, detail="Service unavailable")
    
    async def _check_rate_limit(self, request: Request, routing_rule: Dict[str, Any]) -> bool:
        """Check rate limiting for the request."""
        # Simple in-memory rate limiting (in production, use Redis)
        client_ip = request.client.host if request.client else "unknown"
        rate_limit_key = f"{client_ip}:{request.url.path}"
        
        current_time = datetime.utcnow()
        rate_limit = routing_rule.get("rate_limit", 100)
        
        if rate_limit_key not in self.rate_limiters:
            self.rate_limiters[rate_limit_key] = {
                "count": 0,
                "reset_time": current_time.replace(hour=current_time.hour + 1, minute=0, second=0, microsecond=0)
            }
        
        limiter = self.rate_limiters[rate_limit_key]
        
        # Reset counter if hour has passed
        if current_time >= limiter["reset_time"]:
            limiter["count"] = 0
            limiter["reset_time"] = current_time.replace(hour=current_time.hour + 1, minute=0, second=0, microsecond=0)
        
        # Check if limit exceeded
        if limiter["count"] >= rate_limit:
            return False
        
        # Increment counter
        limiter["count"] += 1
        return True
    
    async def _get_cached_response(self, request: Request) -> Optional[JSONResponse]:
        """Get cached response if available."""
        cache_key = f"{request.method}:{request.url.path}:{request.url.query}"
        if cache_key in self.cache:
            cached_data = self.cache[cache_key]
            if datetime.utcnow() < cached_data["expires_at"]:
                return cached_data["response"]
            else:
                # Remove expired cache entry
                del self.cache[cache_key]
        return None
    
    async def _cache_response(self, request: Request, response: JSONResponse, ttl: int):
        """Cache the response."""
        cache_key = f"{request.method}:{request.url.path}:{request.url.query}"
        expires_at = datetime.utcnow().replace(second=datetime.utcnow().second + ttl)
        
        self.cache[cache_key] = {
            "response": response,
            "expires_at": expires_at
        }
    
    async def get_gateway_status(self) -> Dict[str, Any]:
        """Get the current status of the API Gateway."""
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "routing_rules": len(self.routing_rules),
            "cached_responses": len(self.cache),
            "rate_limiters": len(self.rate_limiters),
            "service_registry": await self.service_registry.get_registry_status()
        }


# Global API Gateway instance
api_gateway: Optional[APIGateway] = None


async def get_api_gateway() -> APIGateway:
    """Dependency for getting API Gateway."""
    global api_gateway
    if api_gateway is None:
        service_registry = await get_service_registry()
        api_gateway = APIGateway(service_registry)
    return api_gateway


async def initialize_api_gateway():
    """Initialize the API Gateway."""
    global api_gateway
    service_registry = await get_service_registry()
    api_gateway = APIGateway(service_registry)
    logger.info("API Gateway initialized")


class GatewayMiddleware:
    """Middleware for API Gateway functionality."""
    
    def __init__(self, api_gateway: APIGateway):
        self.api_gateway = api_gateway
    
    async def __call__(self, request: Request, call_next):
        """Process request through the gateway."""
        # Check if this is a route that should go through the gateway
        path = request.url.path
        
        # Skip gateway for health checks and internal routes
        if path in ["/health", "/health/ai", "/gateway/status"] or path.startswith("/docs"):
            return await call_next(request)
        
        # Check if this should be routed through the gateway
        routing_rule = self.api_gateway.get_routing_rule(path)
        if routing_rule:
            try:
                return await self.api_gateway.route_request(request)
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Gateway routing error: {e}")
                raise HTTPException(status_code=503, detail="Gateway error")
        
        # Continue with normal processing
        return await call_next(request)

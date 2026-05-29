from collections import defaultdict
from datetime import datetime, timedelta
from typing import Callable

from fastapi import HTTPException, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple in-memory rate limiting middleware."""
    
    def __init__(
        self,
        app,
        requests_per_minute: int = 60,
        requests_per_hour: int = 1000,
    ):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self.minute_requests: dict[str, list[datetime]] = defaultdict(list)
        self.hour_requests: dict[str, list[datetime]] = defaultdict(list)
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request."""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"
    
    def _clean_old_requests(self, requests: list[datetime], window: timedelta) -> list[datetime]:
        """Remove requests older than the time window."""
        cutoff = datetime.now() - window
        return [req_time for req_time in requests if req_time > cutoff]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Check rate limits before processing request."""
        # Skip rate limiting for health checks
        if request.url.path in ["/api/health", "/api/ready", "/"]:
            return await call_next(request)
        
        client_ip = self._get_client_ip(request)
        now = datetime.now()
        
        # Clean old requests
        self.minute_requests[client_ip] = self._clean_old_requests(
            self.minute_requests[client_ip],
            timedelta(minutes=1)
        )
        self.hour_requests[client_ip] = self._clean_old_requests(
            self.hour_requests[client_ip],
            timedelta(hours=1)
        )
        
        # Check minute limit
        if len(self.minute_requests[client_ip]) >= self.requests_per_minute:
            logger.warning(f"Rate limit exceeded (minute) for {client_ip}")
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded: {self.requests_per_minute} requests per minute"
            )
        
        # Check hour limit
        if len(self.hour_requests[client_ip]) >= self.requests_per_hour:
            logger.warning(f"Rate limit exceeded (hour) for {client_ip}")
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded: {self.requests_per_hour} requests per hour"
            )
        
        # Record this request
        self.minute_requests[client_ip].append(now)
        self.hour_requests[client_ip].append(now)
        
        response = await call_next(request)
        
        # Add rate limit headers
        response.headers["X-RateLimit-Limit-Minute"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining-Minute"] = str(
            self.requests_per_minute - len(self.minute_requests[client_ip])
        )
        response.headers["X-RateLimit-Limit-Hour"] = str(self.requests_per_hour)
        response.headers["X-RateLimit-Remaining-Hour"] = str(
            self.requests_per_hour - len(self.hour_requests[client_ip])
        )
        
        return response

# Made with Bob
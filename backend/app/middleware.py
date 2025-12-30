from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import logging

logger = logging.getLogger(__name__)

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add security headers including cache-control.
    
    FIX: Prevents browser from caching authenticated pages.
    After logout, back button will not show cached protected pages.
    """
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Paths that should never be cached
        protected_paths = ['/dashboard', '/expenses', '/categories', '/budgets', '/recurring']
        
        # Check if current path is protected
        is_protected = any(request.url.path.startswith(path) for path in protected_paths)
        
        if is_protected:
            # Add cache-control headers to prevent caching
            response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'
            
            logger.debug(f"Cache-control headers added for: {request.url.path}")
        
        # Additional security headers
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        
        return response
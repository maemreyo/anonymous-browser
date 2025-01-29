from typing import TypeVar, Callable, Optional, Dict, Any
import asyncio
from datetime import datetime, timedelta
import logging
from functools import wraps
import time
from dataclasses import dataclass
import aiohttp
from aiohttp import ClientTimeout

logger = logging.getLogger(__name__)

T = TypeVar('T')  # Generic type for return value

@dataclass
class RetryConfig:
    max_attempts: int = 3
    base_delay: float = 1.0  # seconds
    max_delay: float = 10.0  # seconds
    exponential_base: float = 2
    jitter: float = 0.1

@dataclass
class RateLimitConfig:
    requests_per_minute: int = 60
    burst_size: int = 10
    window_size: int = 60  # seconds

@dataclass
class TimeoutConfig:
    connect: float = 10.0  # seconds
    read: float = 30.0     # seconds
    total: float = 60.0    # seconds

class RequestHandler:
    """Handles request retries, rate limiting and timeouts"""
    
    def __init__(
        self,
        retry_config: Optional[RetryConfig] = None,
        rate_limit_config: Optional[RateLimitConfig] = None,
        timeout_config: Optional[TimeoutConfig] = None
    ):
        self.retry_config = retry_config or RetryConfig()
        self.rate_limit_config = rate_limit_config or RateLimitConfig()
        self.timeout_config = timeout_config or TimeoutConfig()
        
        # Rate limiting state
        self._request_timestamps = []
        self._last_request_time = 0.0
        
        # Retry state
        self._retry_counts: Dict[str, int] = {}
        
    async def execute(
        self,
        operation: Callable[..., T],
        *args,
        retry_key: Optional[str] = None,
        **kwargs
    ) -> T:
        """Execute operation with retry, rate limit and timeout handling"""
        
        retry_key = retry_key or operation.__name__
        attempt = 0
        last_error = None
        
        while attempt < self.retry_config.max_attempts:
            try:
                # Check rate limit
                await self._wait_for_rate_limit()
                
                # Execute with timeout
                return await asyncio.wait_for(
                    operation(*args, **kwargs),
                    timeout=self.timeout_config.total
                )
                
            except asyncio.TimeoutError:
                last_error = f"Operation timed out after {self.timeout_config.total}s"
                logger.warning(f"Timeout on attempt {attempt + 1} for {retry_key}")
                
            except Exception as e:
                last_error = str(e)
                logger.warning(f"Error on attempt {attempt + 1} for {retry_key}: {e}")
            
            # Update rate limiting state
            self._update_request_count()
            
            # Calculate retry delay
            delay = self._calculate_retry_delay(attempt)
            
            attempt += 1
            if attempt < self.retry_config.max_attempts:
                logger.info(f"Retrying {retry_key} in {delay:.2f}s (attempt {attempt + 1})")
                await asyncio.sleep(delay)
        
        raise Exception(f"Operation failed after {attempt} attempts. Last error: {last_error}")
    
    def _calculate_retry_delay(self, attempt: int) -> float:
        """Calculate exponential backoff with jitter"""
        delay = min(
            self.retry_config.base_delay * (self.retry_config.exponential_base ** attempt),
            self.retry_config.max_delay
        )
        
        # Add jitter
        jitter = self.retry_config.jitter * delay * (2 * random.random() - 1)
        return max(0, delay + jitter)
    
    async def _wait_for_rate_limit(self) -> None:
        """Wait if rate limit is exceeded"""
        now = time.time()
        
        # Remove old timestamps
        window_start = now - self.rate_limit_config.window_size
        self._request_timestamps = [
            ts for ts in self._request_timestamps
            if ts > window_start
        ]
        
        # Check if we're over the limit
        if len(self._request_timestamps) >= self.rate_limit_config.requests_per_minute:
            # Calculate wait time
            oldest_timestamp = self._request_timestamps[0]
            wait_time = self.rate_limit_config.window_size - (now - oldest_timestamp)
            if wait_time > 0:
                logger.debug(f"Rate limit reached, waiting {wait_time:.2f}s")
                await asyncio.sleep(wait_time)
    
    def _update_request_count(self) -> None:
        """Update rate limiting state"""
        self._request_timestamps.append(time.time())
        
    async def make_request(
        self,
        url: str,
        method: str = "GET",
        **kwargs
    ) -> aiohttp.ClientResponse:
        """Make HTTP request with retry and rate limiting"""
        
        async def _do_request():
            timeout = ClientTimeout(
                connect=self.timeout_config.connect,
                sock_read=self.timeout_config.read,
                total=self.timeout_config.total
            )
            
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.request(method, url, **kwargs) as response:
                    await response.read()
                    return response
        
        return await self.execute(
            _do_request,
            retry_key=f"{method}:{url}"
        )

# Decorator for retry handling
def with_retry(
    retry_config: Optional[RetryConfig] = None,
    rate_limit_config: Optional[RateLimitConfig] = None,
    timeout_config: Optional[TimeoutConfig] = None
):
    handler = RequestHandler(retry_config, rate_limit_config, timeout_config)
    
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await handler.execute(func, *args, **kwargs)
        return wrapper
    return decorator 
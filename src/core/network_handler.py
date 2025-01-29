from typing import Dict, List, Optional, Union, Callable, Any, Set
from enum import Enum
import logging
import json
import re
from playwright.async_api import Route, Request

logger = logging.getLogger(__name__)

class RequestType(Enum):
    DOCUMENT = "document"
    STYLESHEET = "stylesheet" 
    IMAGE = "image"
    MEDIA = "media"
    FONT = "font"
    SCRIPT = "script"
    XHR = "xhr"
    FETCH = "fetch"
    WEBSOCKET = "websocket"
    OTHER = "other"

class NetworkRequestHandler:
    """
    Handles automatic network request management using Playwright's capabilities
    """
    def __init__(self, 
                 block_trackers: bool = True,
                 block_media: bool = False,  # Don't block media by default
                 block_images: bool = False,  # Don't block images by default
                 allowed_domains: Optional[Set[str]] = None):
        self.blocked_resources: List[str] = []
        self.request_filters: Dict[str, Callable] = {}
        self.response_handlers: Dict[str, Callable] = {}
        self.block_trackers = block_trackers
        self.block_media = block_media
        self.block_images = block_images
        self.allowed_domains = allowed_domains or set()
        
        # Initialize default trackers to block if enabled
        if self.block_trackers:
            self._init_tracker_blocklist()

    def _init_tracker_blocklist(self):
        """Initialize list of trackers to block"""
        self.tracker_domains = {
            "google-analytics.com",
            "doubleclick.net",
            "facebook.com/tr",
            "google-analytics",
            "googletagmanager.com",
            "hotjar.com",
            "analytics"
        }

    def is_allowed_domain(self, url: str) -> bool:
        """Check if domain is in allowed list"""
        if not self.allowed_domains:
            return True
        try:
            from urllib.parse import urlparse
            domain = urlparse(url).netloc
            return domain in self.allowed_domains
        except:
            return True

    async def setup_request_interception(self, context) -> None:
        """Setup network request interception for a browser context"""
        if context:
            # Use proper async route handling
            await context.route("**/*", self._handle_route)
            logger.debug("Network request interception setup complete")
        else:
            logger.error("Context is None, cannot setup request interception")
            raise ValueError("Browser context is not initialized")

    async def _handle_route(self, route: Route) -> None:
        """Main route handler with performance optimizations"""
        try:
            request = route.request
            resource_type = request.resource_type
            url = request.url

            # Quick check for allowed domains
            if not self.is_allowed_domain(url):
                await route.continue_()
                return

            # Performance optimization: continue early for essential resources
            if resource_type in [RequestType.DOCUMENT.value, RequestType.STYLESHEET.value]:
                await route.continue_()
                return

            # Check if request should be blocked
            if self._should_block_request(url, resource_type):
                await route.abort()
                logger.debug(f"Blocked request to: {url}")
                return

            # Apply custom filters
            modified_request = self._apply_request_filters(request)
            if modified_request:
                await route.continue_(
                    headers=modified_request.get("headers"),
                    post_data=modified_request.get("post_data")
                )
                return

            # Continue with default behavior
            await route.continue_()
            
        except Exception as e:
            logger.error(f"Error handling route: {str(e)}")
            await route.continue_()

    def _should_block_request(self, url: str, resource_type: str) -> bool:
        """Determine if request should be blocked based on configuration"""
        # Check trackers
        if self.block_trackers and any(tracker in url.lower() for tracker in self.tracker_domains):
            return True
            
        # Check resource types based on configuration
        if resource_type == RequestType.MEDIA.value and self.block_media:
            return True
            
        if resource_type == RequestType.IMAGE.value and self.block_images:
            return True
            
        return False

    def _apply_request_filters(self, request: Request) -> Optional[Dict[str, Any]]:
        """Apply custom request filters"""
        url = request.url
        
        for pattern, filter_func in self.request_filters.items():
            if re.match(pattern, url):
                try:
                    return filter_func(request)
                except Exception as e:
                    logger.error(f"Error applying request filter: {str(e)}")
                    return None
        
        return None

    def add_request_filter(
        self,
        url_pattern: str,
        filter_func: Callable[[Request], Optional[Dict[str, Any]]]
    ) -> None:
        """Add custom request filter"""
        self.request_filters[url_pattern] = filter_func
        
    def add_response_handler(
        self,
        url_pattern: str,
        handler_func: Callable
    ) -> None:
        """Add custom response handler"""
        self.response_handlers[url_pattern] = handler_func

    def block_resource(self, resource: Union[str, List[str]]) -> None:
        """Add resources to block list"""
        if isinstance(resource, str):
            self.blocked_resources.append(resource)
        else:
            self.blocked_resources.extend(resource)

    def allow_domain(self, domain: str) -> None:
        """Add domain to allowed list"""
        self.allowed_domains.add(domain)

    def set_blocking_options(self,
                           block_trackers: Optional[bool] = None,
                           block_media: Optional[bool] = None,
                           block_images: Optional[bool] = None) -> None:
        """Update blocking options dynamically"""
        if block_trackers is not None:
            self.block_trackers = block_trackers
        if block_media is not None:
            self.block_media = block_media
        if block_images is not None:
            self.block_images = block_images 
from typing import Optional, Dict, Any
from browserforge.fingerprints import FingerprintGenerator, Screen
from browserforge.headers import HeaderGenerator, Browser
from ..config.device_specs import DeviceProfileManager, DeviceType, BrowserFamily
from ..config.locale_specs import LocaleManager
from ..config.header_rules import HeaderRuleManager
from .network_handler import NetworkRequestHandler
import logging
import uuid

logger = logging.getLogger(__name__)


class AnonymousFingerprint:
    def __init__(self) -> None:
        self.device_manager = DeviceProfileManager()
        self.locale_manager = LocaleManager()
        
        # Initialize with default configuration
        default_device = self.device_manager.get_device_config()
        default_locale = self.locale_manager.get_locale_config(
            browser=default_device["browser"]["family"],
            device_type=default_device["device_type"]
        )
        
        self.screen = Screen(
            min_width=default_device["screen"]["width_range"][0],
            max_width=default_device["screen"]["width_range"][1],
            min_height=default_device["screen"]["height_range"][0],
            max_height=default_device["screen"]["height_range"][1]
        )
        
        # Initialize generators with locale support
        self.header_generator = HeaderGenerator(
            browser=default_device["browser"]["family"],
            os=default_device["os"],
            device=default_device["device_type"],
            locale=default_locale["locale"],
            http_version=default_locale["http_version"],
            strict=False
        )
        
        self.fingerprint_generator = FingerprintGenerator(
            screen=self.screen,
            strict=False,
            mock_webrtc=True,
            slim=False
        )
        
        self.header_manager = HeaderRuleManager()
        self.network_handler = NetworkRequestHandler()

    async def setup_browser_context(self, context) -> None:
        """Setup browser context with network handling"""
        # Setup network interception
        await self.network_handler.setup_request_interception(context)
        
        # Add custom request filters
        self.network_handler.add_request_filter(
            r".*api\.example\.com.*",
            self._modify_api_request
        )
        
        # Block unnecessary resources
        self.network_handler.block_resource([
            "analytics",
            "advertising",
            "tracking"
        ])

    def _modify_api_request(self, request) -> Dict[str, Any]:
        """Example custom request modifier"""
        headers = request.headers
        # Add custom headers
        headers.update({
            "X-Custom-Header": "value",
            "X-Request-ID": str(uuid.uuid4())
        })
        return {"headers": headers}

    async def generate(
        self,
        device_type: Optional[str] = None,
        preferred_locale: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate fingerprint asynchronously"""
        try:
            device_config = self.device_manager.get_device_config(device_type)
            locale_config = self.locale_manager.get_locale_config(
                browser=device_config["browser"]["family"],
                device_type=device_config["device_type"],
                preferred_locale=preferred_locale
            )
            
            # Generate fingerprint
            fingerprint = self.fingerprint_generator.generate(
                browser=device_config["browser"]["family"]
            )
            
            # Generate headers
            headers = self.header_manager.generate_headers(
                browser=device_config["browser"]["family"],
                version=device_config["browser"].get("version")
            )
            
            return {
                "fingerprint": {
                    "userAgent": headers.get("User-Agent", ""),
                    "viewport": {
                        "width": device_config["screen"]["width_range"][0],
                        "height": device_config["screen"]["height_range"][0]
                    }
                },
                "headers": headers,
                "locale_info": locale_config
            }
            
        except Exception as e:
            logger.error(f"Failed to generate fingerprint: {str(e)}")
            raise

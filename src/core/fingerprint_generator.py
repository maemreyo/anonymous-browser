from typing import Optional, Dict, Any
from browserforge.fingerprints import FingerprintGenerator, Screen
from browserforge.headers import HeaderGenerator, Browser
from ..config.device_specs import DeviceProfileManager, DeviceType, BrowserFamily
from ..config.locale_specs import LocaleManager
import logging

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

    def generate(
        self,
        device_type: Optional[str] = None,
        preferred_locale: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate fingerprint with specific device type and locale"""
        try:
            device_config = self.device_manager.get_device_config(device_type)
            
            locale_config = self.locale_manager.get_locale_config(
                browser=device_config["browser"]["family"],
                device_type=device_config["device_type"],
                preferred_locale=preferred_locale
            )
            
            # Generate fingerprint with locale settings
            fingerprint = self.fingerprint_generator.generate(
                browser=device_config["browser"]["family"]
            )
            
            # Generate headers with locale settings
            headers = self.header_generator.generate(
                browser=device_config["browser"]["family"],
                os=device_config["os"],
                device=device_config["device_type"],
                locale=locale_config["locale"],
                http_version=locale_config["http_version"]
            )
            
            return {
                "fingerprint": fingerprint,
                "headers": headers,
                "locale_info": locale_config
            }

        except Exception as e:
            logger.error(f"Failed to generate fingerprint: {str(e)}")
            raise

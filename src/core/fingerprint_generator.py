from typing import Optional, Dict, Any
from browserforge.fingerprints import FingerprintGenerator, Screen
from browserforge.headers import HeaderGenerator, Browser
from ..config.device_specs import DeviceProfileManager, DeviceType, BrowserFamily
import logging

logger = logging.getLogger(__name__)


class AnonymousFingerprint:
    def __init__(self) -> None:
        self.device_manager = DeviceProfileManager(default_device_type=DeviceType.DESKTOP)
        
        # Get default configuration (Desktop Firefox)
        self.default_config = self.device_manager.get_device_config(
            browser_family=BrowserFamily.FIREFOX
        )
        
        self.screen = Screen(
            min_width=self.default_config["screen"]["width_range"][0],
            max_width=self.default_config["screen"]["width_range"][1],
            min_height=self.default_config["screen"]["height_range"][0],
            max_height=self.default_config["screen"]["height_range"][1]
        )
        
        browser = Browser(
            name=self.default_config["browser"]["family"],
            min_version=self.default_config["browser"]["min_version"],
            max_version=self.default_config["browser"]["max_version"]
        )
        
        self.header_generator = HeaderGenerator(
            browser=browser,
            os=self.default_config["os"],
            device=self.default_config["device_type"],
            strict=False
        )
        
        self.fingerprint_generator = FingerprintGenerator(
            screen=self.screen,
            strict=False,
            mock_webrtc=True,
            slim=False
        )

    def generate(self, device_type: Optional[str] = None) -> Dict[str, Any]:
        """Generate fingerprint with specific device type"""
        try:
            # Get device configuration
            device_config = self.device_manager.get_device_config(device_type)
            
            if not self.device_manager.validate_config(device_config):
                raise ValueError("Invalid device configuration")
                
            # Generate fingerprint with device-specific settings
            fingerprint = self.fingerprint_generator.generate(
                browser=device_config["browser"]["family"]
            )
            
            # Generate matching headers
            headers = self.header_generator.generate(
                browser=device_config["browser"]["family"],
                os=device_config["os"],
                device=device_config["device_type"]
            )
            
            logger.debug(f"Generated fingerprint for {device_config['device_type']}")
            
            return {
                "fingerprint": fingerprint,
                "headers": headers
            }

        except Exception as e:
            logger.error(f"Failed to generate fingerprint: {str(e)}")
            raise

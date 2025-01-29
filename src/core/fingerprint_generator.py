from typing import Optional, Dict, Any
from browserforge.fingerprints import FingerprintGenerator, Screen
from browserforge.headers import HeaderGenerator, Browser
from ..config.settings import BROWSER_CONFIG, SCREEN_CONFIG
from ..config.browser_specs import BROWSER_SPECIFICATIONS
import random
import logging

logger = logging.getLogger(__name__)


class AnonymousFingerprint:
    def __init__(self) -> None:
        self.screen = Screen(
            min_width=SCREEN_CONFIG["min_width"],
            max_width=SCREEN_CONFIG["max_width"],
            min_height=SCREEN_CONFIG["min_height"],
            max_height=SCREEN_CONFIG["max_height"]
        )
        
        # Create browser specifications
        self.browsers = [
            Browser(
                name=browser_name,
                min_version=specs["min_version"],
                max_version=specs["max_version"],
                http_version=specs["http_version"]
            )
            for browser_name, specs in BROWSER_SPECIFICATIONS.items()
        ]
        
        # Initialize generators with more relaxed constraints
        self.header_generator = HeaderGenerator(
            browser=self.browsers,  # Pass browser specifications
            os=BROWSER_CONFIG["os"],
            device=BROWSER_CONFIG["device"],
            locale=BROWSER_CONFIG["locale"],
            http_version=2,
            strict=False  # Relax constraints
        )
        
        self.fingerprint_generator = FingerprintGenerator(
            screen=self.screen,
            strict=False,  # Relax constraints
            mock_webrtc=True,
            slim=False
        )

    def generate(self) -> Dict[str, Any]:
        """Generate a new anonymous fingerprint configuration with retry logic"""
        max_retries = 3
        current_try = 0

        while current_try < max_retries:
            try:
                # Select a random browser specification
                selected_browser = random.choice(self.browsers)
                
                # Generate headers first
                headers = self.header_generator.generate(
                    browser=selected_browser,
                    strict=False
                )
                
                # Use the same browser settings for fingerprint
                fingerprint = self.fingerprint_generator.generate(
                    browser=selected_browser.name,
                    # Remove device_memory and hardware_concurrency
                )
                
                logger.debug(f"Successfully generated fingerprint for {selected_browser.name}")
                
                return {
                    "fingerprint": fingerprint,
                    "headers": headers
                }

            except ValueError as e:
                current_try += 1
                logger.warning(f"Attempt {current_try}/{max_retries} failed: {str(e)}")
                
                if current_try >= max_retries:
                    logger.error("Failed to generate valid fingerprint after max retries")
                    raise

            except Exception as e:
                logger.error(f"Unexpected error: {str(e)}")
                raise

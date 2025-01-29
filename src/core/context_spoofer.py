from typing import Dict, Optional, Any, Union
from enum import Enum
import logging
import json
from datetime import datetime
import pytz
from pathlib import Path
from ..config.spoof_profiles import SpoofingProfiles, TIMEZONE_COORDINATES
from ..config.geolocation_profiles import GeolocationProfiles, GeoLocation
from ..config.proxy_profiles import ProxyProfiles
from .network_handler import NetworkRequestHandler
from ..config.proxy_manager import ProxyManager

logger = logging.getLogger(__name__)


class SpooferType(Enum):
    TIMEZONE = "timezone"
    AUDIO = "audio"
    GEOLOCATION = "geolocation"
    PROXY = "proxy"


class ContextSpoofer:
    """
    Handles timezone and audio context spoofing using Playwright's capabilities
    """

    def __init__(self, network_handler=None):
        self.profiles = SpoofingProfiles()
        self.geo_profiles = GeolocationProfiles()
        self.proxy_profiles = ProxyProfiles()
        self.proxy_manager = ProxyManager()
        self.network_handler = network_handler or NetworkRequestHandler()
        self.spoof_configs = self._load_random_config()
        self._validate_configs()

    def _load_random_config(self) -> Dict[str, Dict[str, Any]]:
        """Load random profile configuration"""
        profile = self.profiles.get_random_profile()

        # Get matching geolocation and proxy for timezone
        geo_location, timezone, locale = self.geo_profiles.get_random_location(
            profile["timezone"].get("timezone_id")
        )

        # Get proxy from matching region
        region = timezone.split("/")[0].upper()
        proxy = self.proxy_profiles.get_random_proxy(region)

        return {
            SpooferType.TIMEZONE.value: profile["timezone"],
            SpooferType.AUDIO.value: profile["audio"],
            SpooferType.GEOLOCATION.value: {
                "enabled": True,
                "location": geo_location.to_dict(),
                "timezone": timezone,
                "locale": locale,
            },
            SpooferType.PROXY.value: {"enabled": True, "config": proxy.to_dict()},
        }

    def _validate_configs(self) -> None:
        """Validate all configurations"""
        if SpooferType.TIMEZONE.value in self.spoof_configs:
            self._validate_timezone_config(
                self.spoof_configs[SpooferType.TIMEZONE.value]
            )
        if SpooferType.AUDIO.value in self.spoof_configs:
            self._validate_audio_config(self.spoof_configs[SpooferType.AUDIO.value])

    async def setup_spoofing(self, context) -> None:
        """Setup context spoofing and show configurations"""
        if not context:
            raise ValueError("Browser context is not initialized")

        try:
            # Setup proxy with proper error handling
            if self.network_handler:
                # First try to setup proxy
                proxy_setup = await self.network_handler.setup_proxy()
                if proxy_setup:
                    # Get proxy config only if setup was successful
                    proxy_config = self.network_handler.get_proxy_config()
                    if proxy_config:
                        logger.info(f"Setting up proxy: {proxy_config.get('server')}")
                        # Create new context with proxy
                        context = await context.browser.new_context(proxy=proxy_config)
                    else:
                        logger.warning("Proxy setup succeeded but no config available")
                else:
                    logger.warning("Failed to setup proxy, continuing without proxy")

            # Add script to show configuration in all pages
            await context.add_init_script("""
                window.showBrowserConfig = async function() {
                    try {
                        let ipData = { ip: 'Checking...' };
                        try {
                            const ipResponse = await fetch('https://api.ipify.org?format=json', {
                                timeout: 5000
                            });
                            ipData = await ipResponse.json();
                        } catch (error) {
                            console.warn('Failed to fetch IP:', error);
                            ipData.ip = 'Failed to fetch';
                        }
                        
                        const config = {
                            'Browser Info': {
                                'User Agent': navigator.userAgent,
                                'Platform': navigator.platform,
                                'Language': navigator.language,
                                'Cookies Enabled': navigator.cookieEnabled
                            },
                            'Network': {
                                'IP Address': ipData.ip,
                                'Connection Type': navigator.connection?.effectiveType || 'Unknown',
                                'Downlink': navigator.connection?.downlink + ' Mbps' || 'Unknown'
                            },
                            'Screen & Hardware': {
                                'Resolution': `${window.screen.width}x${window.screen.height}`,
                                'Color Depth': window.screen.colorDepth + ' bits',
                                'Device Pixel Ratio': window.devicePixelRatio
                            },
                            'Timezone & Location': {
                                'Timezone': Intl.DateTimeFormat().resolvedOptions().timeZone,
                                'Locale': navigator.language
                            }
                        };

                        console.clear();
                        console.log('\\n=== Browser Configuration ===\\n');
                        
                        for (const [category, items] of Object.entries(config)) {
                            console.log(`[${category}]`);
                            for (const [key, value] of Object.entries(items)) {
                                console.log(`${key.padEnd(20)} │ ${value}`);
                            }
                            console.log('');
                        }
                    } catch (error) {
                        console.error('Failed to show configuration:', error);
                    }
                };
                
                // Show config on page load
                showBrowserConfig();
            """)

            # Open new pages for configuration checking
            await self._open_config_pages(context)
            
            logger.info("Context spoofing setup completed")

        except Exception as e:
            logger.error(f"Failed to setup context spoofing: {str(e)}")
            raise

    async def _open_config_pages(self, context) -> None:
        """Open pages to check configuration"""
        try:
            # First try a simple page to verify connection
            test_page = await context.new_page()
            await test_page.goto('http://example.com', timeout=2000)
            await test_page.close()
            
            # If successful, open other pages
            ip_page = await context.new_page()
            await ip_page.goto('https://browserleaks.com/ip', timeout=30000)
            logger.info("Opened IP check page")

            config_page = await context.new_page()
            await config_page.goto('about:blank')
            await config_page.evaluate("showBrowserConfig()")
            logger.info("Opened configuration check page")

        except Exception as e:
            logger.error(f"Failed to open configuration pages: {e}")
            # Don't raise here, allow partial success

    def configure_spoof(self, spoof_type: str, config: Dict[str, Any]) -> None:
        """Configure specific spoof settings"""
        if spoof_type not in self.spoof_configs:
            raise ValueError(f"Invalid spoof type: {spoof_type}")

        self.spoof_configs[spoof_type].update(config)
        logger.debug(f"Updated {spoof_type} spoof configuration: {config}")

    def _validate_timezone_config(self, config: Dict[str, Any]) -> None:
        """Validate timezone configuration"""
        if "timezone_id" in config:
            try:
                import zoneinfo

                zoneinfo.ZoneInfo(config["timezone_id"])
            except Exception as e:
                raise ValueError(f"Invalid timezone: {e}")

    def _validate_audio_config(self, config: Dict[str, Any]) -> None:
        """Validate audio configuration"""
        if "sample_rate" in config:
            if not isinstance(config["sample_rate"], int) or config["sample_rate"] <= 0:
                raise ValueError("Invalid sample rate")
        if "channel_count" in config:
            if (
                not isinstance(config["channel_count"], int)
                or config["channel_count"] <= 0
            ):
                raise ValueError("Invalid channel count")

    def get_spoof_config(self, spoof_type: str) -> Dict[str, Any]:
        """Get current spoof configuration"""
        return self.spoof_configs.get(spoof_type, {})

    def randomize_config(self, device_type: str = None) -> None:
        """Randomize current configuration"""
        profile = self.profiles.get_random_profile(device_type)
        geo_location, timezone, locale = self.geo_profiles.get_random_location(
            profile["timezone"].get("timezone_id")
        )

        self.spoof_configs = {
            SpooferType.TIMEZONE.value: profile["timezone"],
            SpooferType.AUDIO.value: profile["audio"],
            SpooferType.GEOLOCATION.value: {
                "enabled": True,
                "location": geo_location.to_dict(),
                "timezone": timezone,
                "locale": locale,
            },
        }
        self._validate_configs()

    async def log_browser_config(self, context) -> None:
        """Log browser configuration to console"""
        try:
            page = await context.new_page()
            await page.goto("about:blank")
            await page.evaluate("showBrowserConfig()")
            await page.close()
        except Exception as e:
            logger.error(f"Failed to log browser configuration: {e}")
            raise

    async def _get_current_ip(self, context) -> Optional[str]:
        """Get current IP address through proxy"""
        try:
            page = await context.new_page()
            response = await page.goto("https://api.ipify.org?format=json")
            data = await response.json()
            await page.close()
            return data.get("ip")
        except Exception as e:
            logger.error(f"Failed to get IP address: {e}")
            return None

    async def rotate_proxy(self, context, region: Optional[str] = None) -> bool:
        """Rotate proxy for current context"""
        if await self.network_handler.rotate_proxy(region):
            proxy_config = self.network_handler.get_proxy_config()
            if proxy_config:
                await context.route(
                    "**/*", lambda route: route.continue_(proxy=proxy_config)
                )
                return True
        return False

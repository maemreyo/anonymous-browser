from typing import Dict, Optional, Any, Union
from enum import Enum
import logging
import json
from datetime import datetime
import pytz
from pathlib import Path
from ..config.spoof_profiles import SpoofingProfiles, TIMEZONE_COORDINATES

logger = logging.getLogger(__name__)

class SpooferType(Enum):
    TIMEZONE = "timezone"
    AUDIO = "audio"

class ContextSpoofer:
    """
    Handles timezone and audio context spoofing using Playwright's capabilities
    """
    def __init__(self):
        self.profiles = SpoofingProfiles()
        self.spoof_configs = self._load_random_config()
        self._validate_configs()

    def _load_random_config(self) -> Dict[str, Dict[str, Any]]:
        """Load random profile configuration"""
        profile = self.profiles.get_random_profile()
        return {
            SpooferType.TIMEZONE.value: profile["timezone"],
            SpooferType.AUDIO.value: profile["audio"]
        }

    def _validate_configs(self) -> None:
        """Validate all configurations"""
        if SpooferType.TIMEZONE.value in self.spoof_configs:
            self._validate_timezone_config(self.spoof_configs[SpooferType.TIMEZONE.value])
        if SpooferType.AUDIO.value in self.spoof_configs:
            self._validate_audio_config(self.spoof_configs[SpooferType.AUDIO.value])

    async def setup_spoofing(self, context) -> None:
        """Setup context spoofing using Playwright's context options"""
        if not context:
            raise ValueError("Browser context is not initialized")

        try:
            # Get current config
            tz_config = self.spoof_configs["timezone"]
            audio_config = self.spoof_configs["audio"]

            if tz_config["enabled"]:
                # Set timezone and locale using context options
                await context.set_extra_http_headers({
                    "Accept-Language": tz_config["locale"]
                })

                # Get coordinates for the timezone
                lat, lng = TIMEZONE_COORDINATES.get(
                    tz_config["timezone_id"], 
                    (0, 0)  # Default to Greenwich
                )

                # Set geolocation
                await context.grant_permissions(['geolocation'])
                await context.set_geolocation({
                    "latitude": lat,
                    "longitude": lng
                })

                # Inject timezone spoofing script
                await context.add_init_script(f"""
                    // Override timezone-specific JavaScript APIs
                    const originalDate = Date;
                    const timezone = "{tz_config['timezone_id']}";

                    // Override Intl.DateTimeFormat
                    const originalDateTimeFormat = Intl.DateTimeFormat;
                    Intl.DateTimeFormat = function(locales, options = {{}}) {{
                        options.timeZone = timezone;
                        return new originalDateTimeFormat(locales, options);
                    }};

                    // Override date methods
                    const datePrototype = Date.prototype;
                    const originalToString = datePrototype.toString;
                    const originalGetTimezoneOffset = datePrototype.getTimezoneOffset;

                    datePrototype.toString = function() {{
                        return new originalDate(this.valueOf()).toLocaleString('en-US', {{
                            timeZone: timezone
                        }});
                    }};

                    datePrototype.getTimezoneOffset = function() {{
                        const date = new originalDate(this.valueOf());
                        const utcDate = new originalDate(date.toLocaleString('en-US', {{timeZone: 'UTC'}}));
                        const tzDate = new originalDate(date.toLocaleString('en-US', {{timeZone: timezone}}));
                        return (utcDate - tzDate) / 60000;
                    }};
                """)

            if audio_config["enabled"]:
                # Setup audio context
                await context.add_init_script(f"""
                    const SAMPLE_RATE = {audio_config['sample_rate']};
                    const CHANNEL_COUNT = {audio_config['channel_count']};
                    
                    // Override AudioContext
                    const originalAudioContext = window.AudioContext || window.webkitAudioContext;
                    
                    window.AudioContext = window.webkitAudioContext = class extends originalAudioContext {{
                        constructor(options) {{
                            super({{
                                ...options,
                                sampleRate: SAMPLE_RATE
                            }});
                            
                            Object.defineProperty(this, 'destination', {{
                                get: () => {{
                                    const dest = super.destination;
                                    dest.channelCount = CHANNEL_COUNT;
                                    return dest;
                                }}
                            }});
                        }}
                    }};
                """)

            logger.info("Context spoofing setup complete")

        except Exception as e:
            logger.error(f"Failed to setup context spoofing: {str(e)}")
            raise

    def configure_spoof(self, spoof_type: str, config: Dict[str, Any]) -> None:
        """Configure spoofing with validation"""
        if spoof_type not in self.spoof_configs:
            raise ValueError(f"Invalid spoof type: {spoof_type}")
            
        if spoof_type == SpooferType.TIMEZONE.value:
            self._validate_timezone_config(config)
        elif spoof_type == SpooferType.AUDIO.value:
            self._validate_audio_config(config)
            
        self.spoof_configs[spoof_type].update(config)
        logger.debug(f"Updated {spoof_type} configuration: {config}")

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
            if not isinstance(config["channel_count"], int) or config["channel_count"] <= 0:
                raise ValueError("Invalid channel count")

    def get_spoof_config(self, spoof_type: str) -> Dict[str, Any]:
        """Get current spoof configuration"""
        return self.spoof_configs.get(spoof_type, {})

    def randomize_config(self, device_type: str = None) -> None:
        """Randomize current configuration"""
        profile = self.profiles.get_random_profile(device_type)
        self.spoof_configs = {
            SpooferType.TIMEZONE.value: profile["timezone"],
            SpooferType.AUDIO.value: profile["audio"]
        }
        self._validate_configs() 
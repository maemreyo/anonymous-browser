from typing import Dict, Optional, Any, Union
from enum import Enum
import logging
import json
from datetime import datetime
import pytz
from pathlib import Path
from ..config.spoof_profiles import SpoofingProfiles, TIMEZONE_COORDINATES
from ..config.geolocation_profiles import GeolocationProfiles, GeoLocation

logger = logging.getLogger(__name__)

class SpooferType(Enum):
    TIMEZONE = "timezone"
    AUDIO = "audio"
    GEOLOCATION = "geolocation"

class ContextSpoofer:
    """
    Handles timezone and audio context spoofing using Playwright's capabilities
    """
    def __init__(self):
        self.profiles = SpoofingProfiles()
        self.geo_profiles = GeolocationProfiles()
        self.spoof_configs = self._load_random_config()
        self._validate_configs()

    def _load_random_config(self) -> Dict[str, Dict[str, Any]]:
        """Load random profile configuration"""
        profile = self.profiles.get_random_profile()
        
        # Get matching geolocation for timezone
        geo_location, timezone, locale = self.geo_profiles.get_random_location(
            profile["timezone"].get("timezone_id")
        )
        
        return {
            SpooferType.TIMEZONE.value: profile["timezone"],
            SpooferType.AUDIO.value: profile["audio"],
            SpooferType.GEOLOCATION.value: {
                "enabled": True,
                "location": geo_location.to_dict(),
                "timezone": timezone,
                "locale": locale
            }
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
            # Get current configs
            tz_config = self.spoof_configs[SpooferType.TIMEZONE.value]
            audio_config = self.spoof_configs[SpooferType.AUDIO.value]
            geo_config = self.spoof_configs[SpooferType.GEOLOCATION.value]

            # Setup geolocation if enabled
            if geo_config["enabled"]:
                await context.grant_permissions(['geolocation'])
                await context.set_geolocation(geo_config["location"])

            # Setup timezone spoofing (existing code)
            if tz_config["enabled"]:
                await context.set_extra_http_headers({
                    "Accept-Language": tz_config["locale"]
                })

                # Get coordinates for the timezone
                lat, lng = TIMEZONE_COORDINATES.get(
                    tz_config["timezone_id"], 
                    (0, 0)  # Default to Greenwich
                )

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

            # Setup audio spoofing (existing code)
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

            # Update browser logging to include geolocation
            await self.log_browser_config(context)
            
            logger.info("Context spoofing setup complete")

        except Exception as e:
            logger.error(f"Failed to setup context spoofing: {str(e)}")
            raise

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
            if not isinstance(config["channel_count"], int) or config["channel_count"] <= 0:
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
                "locale": locale
            }
        }
        self._validate_configs()

    async def log_browser_config(self, context) -> None:
        """Log all browser configurations to console panel"""
        try:
            await context.add_init_script("""
                function getFlattenedConfig(obj, prefix = '') {
                    let flattened = {};
                    
                    for (const [key, value] of Object.entries(obj)) {
                        if (value === null || value === undefined) continue;
                        
                        if (typeof value === 'object' && !Array.isArray(value)) {
                            const nested = getFlattenedConfig(value, `${prefix}${key}.`);
                            Object.assign(flattened, nested);
                        } else {
                            const displayValue = Array.isArray(value) 
                                ? `[${value.slice(0, 3).join(', ')}${value.length > 3 ? '...' : ''}]`
                                : String(value);
                            flattened[`${prefix}${key}`] = displayValue;
                        }
                    }
                    
                    return flattened;
                }

                function logBrowserConfig() {
                    const config = {
                        // Browser & System
                        'User Agent': navigator.userAgent,
                        'Platform': navigator.platform,
                        'Language': navigator.language,
                        'CPU Cores': navigator.hardwareConcurrency,
                        'Memory': navigator.deviceMemory ? `${navigator.deviceMemory} GB` : 'N/A',
                        
                        // Display
                        'Screen Resolution': `${screen.width}x${screen.height}`,
                        'Color Depth': `${screen.colorDepth}-bit`,
                        'Window Size': `${window.innerWidth}x${window.innerHeight}`,
                        'Device Pixel Ratio': window.devicePixelRatio,
                        
                        // Time & Location
                        'Timezone': Intl.DateTimeFormat().resolvedOptions().timeZone,
                        'Locale': Intl.DateTimeFormat().resolvedOptions().locale,
                        'Time Offset': `UTC${new Date().getTimezoneOffset() >= 0 ? '-' : '+'}${Math.abs(new Date().getTimezoneOffset()/60)}`,
                        
                        // Audio
                        'Audio Sample Rate': (() => {
                            try {
                                const ctx = new (window.AudioContext || window.webkitAudioContext)();
                                return `${ctx.sampleRate} Hz`;
                            } catch (e) {
                                return 'N/A';
                            }
                        })(),
                        
                        // WebGL
                        'WebGL Renderer': (() => {
                            try {
                                const canvas = document.createElement('canvas');
                                const gl = canvas.getContext('webgl');
                                return gl.getParameter(gl.RENDERER);
                            } catch (e) {
                                return 'N/A';
                            }
                        })(),
                        
                        // Network
                        'Network Info': (() => {
                            const conn = navigator.connection;
                            return conn ? `${conn.effectiveType || 'unknown'} (${conn.downlink} Mbps)` : 'N/A';
                        })(),
                        
                        // Spoofed Settings
                        'Spoofed Timezone': window.__SPOOF_CONFIG?.timezone?.timezone_id || 'None',
                        'Spoofed Locale': window.__SPOOF_CONFIG?.timezone?.locale || 'None',
                        'Spoofed Audio Rate': window.__SPOOF_CONFIG?.audio?.sample_rate 
                            ? `${window.__SPOOF_CONFIG.audio.sample_rate} Hz` 
                            : 'None',
                        
                        // Add Geolocation section
                        'Geolocation': {
                            'Latitude': window.__SPOOF_CONFIG?.geolocation?.location?.latitude || 'None',
                            'Longitude': window.__SPOOF_CONFIG?.geolocation?.location?.longitude || 'None',
                            'Accuracy': window.__SPOOF_CONFIG?.geolocation?.location?.accuracy || 'None'
                        }
                    };

                    console.log('\\n=== 🌐 Browser Configuration ===');
                    console.log('══════════════════════════════════');
                    
                    const flatConfig = getFlattenedConfig(config);
                    const maxKeyLength = Math.max(...Object.keys(flatConfig).map(key => key.length));
                    
                    for (const [key, value] of Object.entries(flatConfig)) {
                        const paddedKey = key.padEnd(maxKeyLength);
                        console.log(`${paddedKey} │ ${value}`);
                    }
                    
                    console.log('══════════════════════════════════\\n');
                }

                // Store spoof config globally
                window.__SPOOF_CONFIG = {
                    timezone: %s,
                    audio: %s,
                    geolocation: %s
                };

                // Log the configuration
                logBrowserConfig();
            """ % (
                json.dumps(self.spoof_configs[SpooferType.TIMEZONE.value]),
                json.dumps(self.spoof_configs[SpooferType.AUDIO.value]),
                json.dumps(self.spoof_configs[SpooferType.GEOLOCATION.value])
            ))

            logger.info("Browser configuration logged to console panel")
            
        except Exception as e:
            logger.error(f"Failed to log browser configuration: {str(e)}")
            raise 
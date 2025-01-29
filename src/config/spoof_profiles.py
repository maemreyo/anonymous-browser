from typing import Dict, Any, List, Tuple
from enum import Enum
import json
from pathlib import Path
import random
import logging
from dataclasses import dataclass
import pytz
from zoneinfo import ZoneInfo

logger = logging.getLogger(__name__)

# Predefined timezone coordinates map
TIMEZONE_COORDINATES = {
    "America/New_York": (40.7128, -74.0060),
    "Europe/London": (51.5074, -0.1278),
    "Asia/Tokyo": (35.6762, 139.6503),
    "Europe/Paris": (48.8566, 2.3522),
    "Asia/Singapore": (1.3521, 103.8198),
    "Australia/Sydney": (-33.8688, 151.2093),
    "Asia/Dubai": (25.2048, 55.2708),
    "Europe/Berlin": (52.5200, 13.4050),
    "Asia/Seoul": (37.5665, 126.9780),
    "Europe/Moscow": (55.7558, 37.6173),
    "Asia/Shanghai": (31.2304, 121.4737),
    "Europe/Amsterdam": (52.3676, 4.9041),
    "Asia/Hong_Kong": (22.3193, 114.1694)
}

class DeviceType(Enum):
    DESKTOP = "desktop"
    MOBILE = "mobile"
    TABLET = "tablet"

@dataclass
class AudioProfile:
    sample_rate: int
    channel_count: int
    latency: float
    
    @classmethod
    def get_random(cls) -> 'AudioProfile':
        return cls(
            sample_rate=random.choice([44100, 48000, 96000]),
            channel_count=random.choice([1, 2, 4, 6]),
            latency=round(random.uniform(0.001, 0.015), 3)
        )

@dataclass
class TimezoneProfile:
    timezone_id: str
    locale: str
    geo_location: Dict[str, float]
    
    @classmethod
    def get_random(cls) -> 'TimezoneProfile':
        # Get random timezone from a weighted list
        timezone_weights = {
            "America/New_York": 0.2,
            "Europe/London": 0.15,
            "Asia/Tokyo": 0.1,
            "Europe/Paris": 0.1,
            "Asia/Singapore": 0.05,
            "Australia/Sydney": 0.05,
            "Asia/Dubai": 0.05,
            "Europe/Berlin": 0.05,
            "Asia/Seoul": 0.05,
            "Europe/Moscow": 0.05,
            "Asia/Shanghai": 0.05,
            "Europe/Amsterdam": 0.05,
            "Asia/Hong_Kong": 0.05
        }
        
        timezone_id = random.choices(
            list(timezone_weights.keys()),
            weights=list(timezone_weights.values())
        )[0]
        
        # Match locale to timezone region
        locale_map = {
            "America": ["en-US", "en-CA", "es-MX"],
            "Europe": ["en-GB", "fr-FR", "de-DE", "es-ES", "nl-NL", "ru-RU"],
            "Asia": ["ja-JP", "zh-CN", "ko-KR", "zh-TW", "zh-HK", "ar-AE"],
            "Australia": ["en-AU"]
        }
        region = timezone_id.split('/')[0]
        locale = random.choice(locale_map.get(region, ["en-US"]))
        
        # Get base coordinates for timezone
        base_lat, base_lng = TIMEZONE_COORDINATES[timezone_id]
        
        # Add small random offset (±0.1 degrees) to prevent fingerprinting
        lat = base_lat + random.uniform(-0.1, 0.1)
        lng = base_lng + random.uniform(-0.1, 0.1)
        
        return cls(
            timezone_id=timezone_id,
            locale=locale,
            geo_location={"latitude": round(lat, 4), "longitude": round(lng, 4)}
        )

class SpoofingProfiles:
    """Manages spoofing profiles with smart randomization"""
    
    def __init__(self):
        self.config_path = Path("config/spoof_profiles.json")
        self.profiles = self._load_profiles()
        
    def _load_profiles(self) -> Dict[str, List[Dict[str, Any]]]:
        """Load profiles from config file or generate defaults"""
        try:
            if self.config_path.exists():
                with open(self.config_path) as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load profiles: {e}")
            
        return self._generate_default_profiles()
        
    def _generate_default_profiles(self) -> Dict[str, List[Dict[str, Any]]]:
        """Generate diverse default profiles"""
        profiles = {
            DeviceType.DESKTOP.value: [],
            DeviceType.MOBILE.value: [],
            DeviceType.TABLET.value: []
        }
        
        # Generate profiles for each device type
        for device_type in DeviceType:
            for _ in range(10):  # Generate 10 profiles per type
                timezone = TimezoneProfile.get_random()
                audio = AudioProfile.get_random()
                
                profile = {
                    "name": f"{device_type.value}_{_}",
                    "timezone": {
                        "enabled": True,
                        "timezone_id": timezone.timezone_id,
                        "locale": timezone.locale,
                        "geo_location": timezone.geo_location
                    },
                    "audio": {
                        "enabled": True,
                        "sample_rate": audio.sample_rate,
                        "channel_count": audio.channel_count,
                        "latency": audio.latency
                    }
                }
                profiles[device_type.value].append(profile)
                
        # Save generated profiles
        self._save_profiles(profiles)
        return profiles
    
    def _save_profiles(self, profiles: Dict[str, List[Dict[str, Any]]]) -> None:
        """Save profiles to config file"""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'w') as f:
                json.dump(profiles, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save profiles: {e}")
            
    def get_random_profile(self, device_type: str = None) -> Dict[str, Any]:
        """Get random profile with smart selection"""
        if device_type and device_type not in self.profiles:
            raise ValueError(f"Invalid device type: {device_type}")
            
        if not device_type:
            device_type = random.choice(list(self.profiles.keys()))
            
        profiles = self.profiles[device_type]
        return random.choice(profiles)
    
    def add_profile(self, device_type: str, profile: Dict[str, Any]) -> None:
        """Add new profile"""
        if device_type not in self.profiles:
            raise ValueError(f"Invalid device type: {device_type}")
            
        self.profiles[device_type].append(profile)
        self._save_profiles(self.profiles)
        
    def remove_profile(self, device_type: str, profile_name: str) -> None:
        """Remove profile by name"""
        if device_type not in self.profiles:
            raise ValueError(f"Invalid device type: {device_type}")
            
        self.profiles[device_type] = [
            p for p in self.profiles[device_type]
            if p["name"] != profile_name
        ]
        self._save_profiles(self.profiles) 
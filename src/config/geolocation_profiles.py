from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
import random
import json
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

@dataclass
class GeoLocation:
    latitude: float
    longitude: float
    accuracy: Optional[float] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GeoLocation':
        return cls(
            latitude=data['latitude'],
            longitude=data['longitude'],
            accuracy=data.get('accuracy')
        )

    def to_dict(self) -> Dict[str, Any]:
        data = {
            'latitude': self.latitude,
            'longitude': self.longitude
        }
        if self.accuracy is not None:
            data['accuracy'] = self.accuracy
        return data

class GeolocationProfiles:
    """Manages geolocation profiles with smart randomization"""
    
    # Common city coordinates with timezone mappings
    CITY_PROFILES = {
        "Tokyo": {
            "coords": GeoLocation(35.6762, 139.6503),
            "timezone": "Asia/Tokyo",
            "locale": "ja-JP",
            "weight": 0.2
        },
        "New_York": {
            "coords": GeoLocation(40.7128, -74.0060),
            "timezone": "America/New_York",
            "locale": "en-US",
            "weight": 0.2
        },
        "London": {
            "coords": GeoLocation(51.5074, -0.1278),
            "timezone": "Europe/London", 
            "locale": "en-GB",
            "weight": 0.15
        },
        # Add more cities with appropriate weights
    }

    def __init__(self):
        self.config_path = Path("config/geolocation_profiles.json")
        self.custom_profiles = self._load_custom_profiles()

    def _load_custom_profiles(self) -> Dict[str, Dict[str, Any]]:
        """Load custom profiles from config file"""
        try:
            if self.config_path.exists():
                with open(self.config_path) as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load custom profiles: {e}")
        return {}

    def get_random_location(self, timezone: Optional[str] = None) -> Tuple[GeoLocation, str, str]:
        """Get random location with matching timezone and locale"""
        if timezone:
            # Filter profiles matching timezone
            matching_profiles = {
                name: profile for name, profile in self.CITY_PROFILES.items()
                if profile["timezone"] == timezone
            }
            if not matching_profiles:
                logger.warning(f"No profiles found for timezone {timezone}, using random")
                matching_profiles = self.CITY_PROFILES
        else:
            matching_profiles = self.CITY_PROFILES

        # Select random profile based on weights
        weights = [profile["weight"] for profile in matching_profiles.values()]
        profile_name = random.choices(list(matching_profiles.keys()), weights=weights)[0]
        profile = matching_profiles[profile_name]

        # Add small random offset to prevent fingerprinting
        coords = profile["coords"]
        randomized_location = GeoLocation(
            latitude=coords.latitude + random.uniform(-0.01, 0.01),
            longitude=coords.longitude + random.uniform(-0.01, 0.01),
            accuracy=random.randint(1, 100)
        )

        return randomized_location, profile["timezone"], profile["locale"]

    def add_custom_profile(self, name: str, profile: Dict[str, Any]) -> None:
        """Add custom geolocation profile"""
        self.custom_profiles[name] = profile
        self._save_custom_profiles()

    def _save_custom_profiles(self) -> None:
        """Save custom profiles to config file"""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'w') as f:
                json.dump(self.custom_profiles, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save custom profiles: {e}") 
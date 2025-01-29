from enum import Enum
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass
import random

class HTTPVersion(Enum):
    HTTP1 = 1
    HTTP2 = 2
    HTTP3 = 3  # Future support

@dataclass
class LocaleConfig:
    code: str
    weight: float  # Frequency weight
    accept_language: str
    time_zone: str
    date_format: str
    number_format: Dict[str, str]

class LocaleManager:
    """Manages locale and HTTP configurations with realistic constraints"""
    
    # Realistic locale configurations based on Browserforge statistics
    LOCALE_SPECS: Dict[str, LocaleConfig] = {
        "en-US": LocaleConfig(
            code="en-US",
            weight=0.35,  # Adjusted weight
            accept_language="en-US,en;q=0.9",
            time_zone="America/New_York",
            date_format="MM/dd/yyyy",
            number_format={
                "decimal": ".",
                "thousands": ",",
                "currency": "$"
            }
        ),
        "en-GB": LocaleConfig(
            code="en-GB",
            weight=0.15,
            accept_language="en-GB,en;q=0.9",
            time_zone="Europe/London",
            date_format="dd/MM/yyyy",
            number_format={
                "decimal": ".",
                "thousands": ",",
                "currency": "£"
            }
        ),
        "de-DE": LocaleConfig(
            code="de-DE",
            weight=0.15,
            accept_language="de-DE,de;q=0.9,en;q=0.8",
            time_zone="Europe/Berlin",
            date_format="dd.MM.yyyy",
            number_format={
                "decimal": ",",
                "thousands": ".",
                "currency": "€"
            }
        ),
        "fr-FR": LocaleConfig(
            code="fr-FR",
            weight=0.12,
            accept_language="fr-FR,fr;q=0.9,en;q=0.8",
            time_zone="Europe/Paris",
            date_format="dd/MM/yyyy",
            number_format={
                "decimal": ",",
                "thousands": " ",
                "currency": "€"
            }
        ),
        "es-ES": LocaleConfig(  # Added Spanish
            code="es-ES",
            weight=0.08,
            accept_language="es-ES,es;q=0.9,en;q=0.8",
            time_zone="Europe/Madrid",
            date_format="dd/MM/yyyy",
            number_format={
                "decimal": ",",
                "thousands": ".",
                "currency": "€"
            }
        ),
        "it-IT": LocaleConfig(  # Added Italian
            code="it-IT",
            weight=0.08,
            accept_language="it-IT,it;q=0.9,en;q=0.8",
            time_zone="Europe/Rome",
            date_format="dd/MM/yyyy",
            number_format={
                "decimal": ",",
                "thousands": ".",
                "currency": "€"
            }
        ),
        "ja-JP": LocaleConfig(  # Added Japanese
            code="ja-JP",
            weight=0.07,
            accept_language="ja-JP,ja;q=0.9,en;q=0.8",
            time_zone="Asia/Tokyo",
            date_format="yyyy/MM/dd",
            number_format={
                "decimal": ".",
                "thousands": ",",
                "currency": "¥"
            }
        )
    }

    # HTTP version compatibility matrix
    HTTP_COMPATIBILITY: Dict[str, Dict[str, List[HTTPVersion]]] = {
        "firefox": {
            "desktop": [HTTPVersion.HTTP1, HTTPVersion.HTTP2],
            "mobile": [HTTPVersion.HTTP1, HTTPVersion.HTTP2]
        },
        "chrome": {
            "desktop": [HTTPVersion.HTTP1, HTTPVersion.HTTP2],
            "mobile": [HTTPVersion.HTTP1, HTTPVersion.HTTP2]
        }
    }

    def __init__(self):
        self._validate_weights()

    def _validate_weights(self):
        """Validate that locale weights sum to approximately 1"""
        total_weight = sum(locale.weight for locale in self.LOCALE_SPECS.values())
        if not 0.99 <= total_weight <= 1.01:
            # Instead of raising error, normalize weights
            self._normalize_weights(total_weight)

    def _normalize_weights(self, total_weight: float):
        """Normalize weights to sum to 1"""
        for locale in self.LOCALE_SPECS.values():
            locale.weight = locale.weight / total_weight

    def get_locale(self, browser: str, device_type: str) -> LocaleConfig:
        """Get appropriate locale based on browser and device type"""
        # Use weighted random selection
        weights = [locale.weight for locale in self.LOCALE_SPECS.values()]
        selected_locale = random.choices(
            list(self.LOCALE_SPECS.values()),
            weights=weights,
            k=1
        )[0]
        return selected_locale

    def get_http_version(
        self,
        browser: str,
        device_type: str,
        preferred_version: Optional[HTTPVersion] = None
    ) -> HTTPVersion:
        """Get compatible HTTP version"""
        compatible_versions = self.HTTP_COMPATIBILITY.get(browser, {}).get(
            device_type,
            [HTTPVersion.HTTP1]  # Fallback to HTTP/1
        )

        if preferred_version in compatible_versions:
            return preferred_version

        return random.choice(compatible_versions)

    def generate_accept_language(self, locale_code: str) -> str:
        """Generate Accept-Language header value"""
        locale = self.LOCALE_SPECS[locale_code]
        return locale.accept_language

    def get_locale_config(
        self,
        browser: str,
        device_type: str,
        preferred_locale: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get complete locale configuration"""
        locale = (
            self.LOCALE_SPECS.get(preferred_locale)
            or self.get_locale(browser, device_type)
        )
        
        http_version = self.get_http_version(browser, device_type)

        return {
            "locale": locale.code,
            "accept_language": locale.accept_language,
            "time_zone": locale.time_zone,
            "date_format": locale.date_format,
            "number_format": locale.number_format,
            "http_version": http_version.value
        } 
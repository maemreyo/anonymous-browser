from typing import Dict, Any

# Browser configuration
BROWSER_CONFIG: Dict[str, Any] = {
    "browser": ("chrome", "firefox", "safari"),  # Supported browsers
    "os": ("windows", "macos", "linux"),  # Supported operating systems
    "device": "desktop",  # Device type
    "locale": ("en-US", "en-GB", "de-DE"),  # Supported locales
    "http_version": 2,  # HTTP version
}

# Screen resolution constraints
SCREEN_CONFIG: Dict[str, int] = {
    "min_width": 1024,
    "max_width": 2560,
    "min_height": 768,
    "max_height": 1440,
}

# Logging configuration
LOGGING_CONFIG: Dict[str, Any] = {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "filename": "browser_activity.log",
} 
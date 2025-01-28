from typing import Dict, Any, Tuple, Union, Literal, List
from browserforge.headers import Browser
from browserforge.fingerprints import Screen, VideoCard
from .constraints import (
    validate_config,
    generate_consistent_config,
    DeviceType,
    OSFamily,
    HARDWARE_CONSTRAINTS,
    OS_BROWSER_CONSTRAINTS
)

# Browser configuration with version ranges
BROWSER_VERSIONS: Dict[str, Dict[str, int]] = {
    "chrome": {"min_version": 100, "max_version": 122},
    "firefox": {"min_version": 100, "max_version": 115},
    "safari": {"min_version": 15, "max_version": 17},
    "edge": {"min_version": 100, "max_version": 121},
}

# Define browser specifications with version constraints
BROWSER_SPECS = [
    Browser(name='chrome', min_version=BROWSER_VERSIONS["chrome"]["min_version"], 
            max_version=BROWSER_VERSIONS["chrome"]["max_version"]),
    Browser(name='firefox', min_version=BROWSER_VERSIONS["firefox"]["min_version"], 
            max_version=BROWSER_VERSIONS["firefox"]["max_version"]),
    Browser(name='safari', min_version=BROWSER_VERSIONS["safari"]["min_version"], 
            max_version=BROWSER_VERSIONS["safari"]["max_version"]),
    Browser(name='edge', min_version=BROWSER_VERSIONS["edge"]["min_version"], 
            max_version=BROWSER_VERSIONS["edge"]["max_version"]),
]

# Browser configuration
BROWSER_CONFIG: Dict[str, Union[List[Browser], Tuple[str, ...], str, int]] = {
    "browser": BROWSER_SPECS,
    "os": ("windows", "macos", "linux", "android", "ios"),
    "device": ("desktop", "mobile", "tablet"),
    "locale": ("en-US", "en-GB", "de-DE", "fr-FR", "es-ES", "ja-JP", "zh-CN"),
    "http_version": 2,
}

# Screen resolution constraints
SCREEN_CONFIG: Dict[str, Any] = {
    "min_width": 1024,
    "max_width": 3840,  # Support 4K displays
    "min_height": 768,
    "max_height": 2160,  # Support 4K displays
    "color_depth": 24,
    "pixel_ratio": (1, 1.5, 2, 2.25, 3),  # Common pixel ratios
}

# Enhanced fingerprint configuration
FINGERPRINT_CONFIG: Dict[str, Any] = {
    "strict": True,  # Raise exception if constraints are too strict
    "mock_webrtc": True,  # Mock WebRTC to prevent leaks
    "slim": False,  # Enable all evasion techniques
    
    # Hardware specifications
    "hardware": {
        "device_memory": (4, 8, 16, 32),  # Common RAM sizes in GB
        "hardware_concurrency": (4, 8, 12, 16),  # CPU threads
        "max_touch_points": (0, 5, 10),  # Touch points (0 for desktop)
    },
    
    # Media devices configuration
    "media_devices": {
        "audio_inputs": (0, 1, 2),  # Number of microphones
        "audio_outputs": (1, 2),    # Number of speakers
        "video_inputs": (0, 1)      # Number of cameras
    },
    
    # Audio/Video codec support
    "codecs": {
        "audio": {
            "aac": "probably",
            "mp3": "probably",
            "ogg": "probably",
            "wav": "probably",
            "m4a": "maybe"
        },
        "video": {
            "h264": "probably",
            "webm": "probably",
            "ogg": "maybe"
        }
    },
    
    # Plugin configuration
    "plugins": {
        "pdf_viewer": True,
        "mock_plugins": True,
        "allowed_plugins": [
            "PDF Viewer",
            "Chrome PDF Viewer",
            "Chromium PDF Viewer",
            "Edge PDF Viewer",
            "WebKit built-in PDF"
        ]
    },
    
    # Battery configuration
    "battery": {
        "charging": (True, False),
        "charging_time": (0, None),
        "discharging_time": (1000, 24000),
        "level": (0.1, 1.0)
    },
    
    # WebGL configuration
    "webgl": {
        "vendors": [
            "Google Inc. (Intel)",
            "Google Inc. (AMD)",
            "Google Inc. (NVIDIA)",
            "Apple (Apple M1)",
            "Apple (Apple M2)"
        ],
        "renderers": [
            "ANGLE (Intel, Intel(R) Iris(R) Xe Graphics Direct3D11 vs_5_0 ps_5_0)",
            "ANGLE (AMD, AMD Radeon RX 6800 XT Direct3D11 vs_5_0 ps_5_0)",
            "ANGLE (NVIDIA, NVIDIA GeForce RTX 3080 Direct3D11 vs_5_0 ps_5_0)",
            "ANGLE (Apple, Apple M1)",
            "ANGLE (Apple, Apple M2)"
        ]
    },
    
    # Font configuration
    "fonts": {
        "common_fonts": [
            "Arial", "Helvetica", "Times New Roman", "Courier New",
            "Verdana", "Georgia", "Calibri", "Segoe UI"
        ],
        "min_fonts": 5,
        "max_fonts": 15
    }
}

# Logging configuration
LOGGING_CONFIG: Dict[str, Any] = {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "filename": "browser_activity.log",
}

# Mark old configuration as deprecated
BROWSER_CONFIG_V1: Dict[str, Any] = {
    "browser": ("chrome", "firefox", "safari"),
    "os": ("windows", "macos", "linux"),
    "device": "desktop",
    "locale": ("en-US", "en-GB", "de-DE"),
    "http_version": 2,
}

def get_fingerprint_config(
    device_type: DeviceType = DeviceType.DESKTOP,
    os_family: OSFamily = OSFamily.WINDOWS
) -> Dict[str, Any]:
    """
    Get a consistent fingerprint configuration for given device type and OS
    
    Args:
        device_type: Type of device
        os_family: Operating system family
        
    Returns:
        Valid fingerprint configuration dictionary
    """
    base_config = generate_consistent_config(device_type, os_family)
    
    # Validate the configuration
    errors = validate_config(base_config)
    if errors:
        raise ValueError(f"Invalid configuration: {', '.join(errors)}")
    
    return base_config

# Example usage:
# config = get_fingerprint_config(DeviceType.MOBILE, OSFamily.ANDROID) 
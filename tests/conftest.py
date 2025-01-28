import pytest
from typing import Dict, Any
from src.config.constraints import DeviceType, OSFamily, BrowserFamily

@pytest.fixture
def sample_device_configs() -> Dict[str, Dict[str, Any]]:
    return {
        "desktop": {
            "device_type": DeviceType.DESKTOP,
            "os_family": OSFamily.WINDOWS,
            "browser_family": BrowserFamily.CHROME,
            "expected_memory": (8, 16, 32),
            "expected_touch": (0,),
            "screen_width_range": (1024, 3840)
        },
        "mobile": {
            "device_type": DeviceType.MOBILE,
            "os_family": OSFamily.ANDROID,
            "browser_family": BrowserFamily.CHROME,
            "expected_memory": (2, 4, 6, 8),
            "expected_touch": (5, 10),
            "screen_width_range": (320, 428)
        }
    }

@pytest.fixture
def mock_fingerprint_config():
    return {
        "device": "desktop",
        "os": "windows",
        "browser": "chrome",
        "device_memory": 8,
        "hardware_concurrency": 4,
        "max_touch_points": 0,
        "screen": {
            "width": 1920,
            "height": 1080,
            "pixel_ratio": 1
        }
    } 
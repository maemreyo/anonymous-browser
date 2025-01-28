import pytest
from src.core.fingerprint_generator import AnonymousFingerprint


@pytest.fixture
def fingerprint_generator():
    return AnonymousFingerprint()

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
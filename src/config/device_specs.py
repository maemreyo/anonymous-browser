from enum import Enum
from typing import Dict, Any, List, Tuple, Optional

class DeviceType(str, Enum):
    DESKTOP = "desktop"
    MOBILE = "mobile"
    TABLET = "tablet"

class OSFamily(str, Enum):
    WINDOWS = "windows"
    MACOS = "macos"
    LINUX = "linux"
    ANDROID = "android"
    IOS = "ios"

class BrowserFamily(str, Enum):
    FIREFOX = "firefox"  # Default browser
    CHROME = "chrome"
    SAFARI = "safari"
    EDGE = "edge"

# Device-specific constraints
DEVICE_SPECIFICATIONS: Dict[str, Dict[str, Any]] = {
    DeviceType.DESKTOP: {
        "screen": {
            "width_range": (1024, 2560),
            "height_range": (768, 1600),
            "pixel_ratio": (1, 1.25, 1.5, 2),
            "color_depth": 24,
        },
        "supported_browsers": [
            BrowserFamily.FIREFOX,  # Preferred default
            BrowserFamily.CHROME,
            BrowserFamily.EDGE,
            BrowserFamily.SAFARI
        ],
        "supported_os": [
            OSFamily.WINDOWS,
            OSFamily.MACOS,
            OSFamily.LINUX
        ],
        "input_capabilities": {
            "touch_enabled": False,
            "max_touch_points": 0,
            "hover": "hover",
            "pointer": "fine"
        }
    },
    DeviceType.MOBILE: {
        "screen": {
            "width_range": (320, 428),
            "height_range": (568, 926),
            "pixel_ratio": (2, 2.5, 3),
            "color_depth": 24,
        },
        "supported_browsers": [
            BrowserFamily.FIREFOX,  # Mobile Firefox
            BrowserFamily.CHROME,
            BrowserFamily.SAFARI
        ],
        "supported_os": [
            OSFamily.ANDROID,
            OSFamily.IOS
        ],
        "input_capabilities": {
            "touch_enabled": True,
            "max_touch_points": 5,
            "hover": "none",
            "pointer": "coarse"
        }
    },
    DeviceType.TABLET: {
        "screen": {
            "width_range": (601, 1024),
            "height_range": (800, 1366),
            "pixel_ratio": (1.5, 2, 2.5),
            "color_depth": 24,
        },
        "supported_browsers": [
            BrowserFamily.FIREFOX,  # Tablet Firefox
            BrowserFamily.CHROME,
            BrowserFamily.SAFARI
        ],
        "supported_os": [
            OSFamily.ANDROID,
            OSFamily.IOS,
            OSFamily.WINDOWS  # For Windows tablets
        ],
        "input_capabilities": {
            "touch_enabled": True,
            "max_touch_points": 10,
            "hover": "hover",
            "pointer": "fine"
        }
    }
}

# OS-Browser version constraints
OS_BROWSER_VERSIONS: Dict[str, Dict[str, Dict[str, int]]] = {
    OSFamily.WINDOWS: {
        BrowserFamily.FIREFOX: {
            "min_version": 115,  # ESR version
            "max_version": 124
        },
        BrowserFamily.CHROME: {
            "min_version": 120,
            "max_version": 122
        }
    },
    OSFamily.LINUX: {
        BrowserFamily.FIREFOX: {
            "min_version": 115,
            "max_version": 124
        }
    },
    OSFamily.ANDROID: {
        BrowserFamily.FIREFOX: {
            "min_version": 115,
            "max_version": 124
        }
    }
}

class DeviceProfileManager:
    """Manages device profiles and ensures configuration consistency"""
    
    def __init__(self, default_device_type: str = DeviceType.DESKTOP):
        self.default_device_type = default_device_type
        
    def get_device_config(
        self,
        device_type: Optional[str] = None,
        browser_family: Optional[str] = None,
        os_family: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get a consistent device configuration based on specified parameters
        """
        device_type = device_type or self.default_device_type
        device_specs = DEVICE_SPECIFICATIONS[device_type]
        
        # Default to Firefox if not specified
        browser_family = browser_family or BrowserFamily.FIREFOX
        
        # Validate and get compatible OS
        if os_family and os_family not in device_specs["supported_os"]:
            raise ValueError(f"OS {os_family} not supported for device type {device_type}")
            
        os_family = os_family or device_specs["supported_os"][0]
        
        # Get browser version constraints
        browser_versions = OS_BROWSER_VERSIONS.get(os_family, {}).get(browser_family, {})
        
        return {
            "device_type": device_type,
            "browser": {
                "family": browser_family,
                "min_version": browser_versions.get("min_version"),
                "max_version": browser_versions.get("max_version")
            },
            "os": os_family,
            "screen": device_specs["screen"],
            "input_capabilities": device_specs["input_capabilities"]
        }

    def validate_config(self, config: Dict[str, Any]) -> bool:
        """
        Validate device configuration consistency
        """
        device_type = config.get("device_type")
        if not device_type or device_type not in DEVICE_SPECIFICATIONS:
            return False
            
        device_specs = DEVICE_SPECIFICATIONS[device_type]
        
        # Validate browser compatibility
        browser = config.get("browser", {}).get("family")
        if browser not in device_specs["supported_browsers"]:
            return False
            
        # Validate OS compatibility
        os = config.get("os")
        if os not in device_specs["supported_os"]:
            return False
            
        return True 
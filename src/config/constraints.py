from enum import Enum
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass

class DeviceType(Enum):
    DESKTOP = "desktop"
    MOBILE = "mobile"
    TABLET = "tablet"

class OSFamily(Enum):
    WINDOWS = "windows"
    MACOS = "macos"
    LINUX = "linux"
    ANDROID = "android"
    IOS = "ios"

class BrowserFamily(Enum):
    CHROME = "chrome"
    FIREFOX = "firefox"
    SAFARI = "safari"
    EDGE = "edge"

@dataclass
class HardwareProfile:
    device_memory: int
    hardware_concurrency: int
    max_touch_points: int
    screen_width: int
    screen_height: int
    pixel_ratio: float

# Define hardware constraints for different device types
HARDWARE_CONSTRAINTS: Dict[DeviceType, Dict[str, Any]] = {
    DeviceType.DESKTOP: {
        "device_memory": (8, 16, 32),
        "hardware_concurrency": (4, 8, 12, 16),
        "max_touch_points": (0,),
        "screen": {
            "width": (1024, 3840),
            "height": (768, 2160),
            "pixel_ratio": (1, 1.5, 2)
        }
    },
    DeviceType.MOBILE: {
        "device_memory": (2, 4, 6, 8),
        "hardware_concurrency": (4, 6, 8),
        "max_touch_points": (5, 10),
        "screen": {
            "width": (320, 428),
            "height": (568, 926),
            "pixel_ratio": (2, 2.25, 3)
        }
    },
    DeviceType.TABLET: {
        "device_memory": (4, 8, 16),
        "hardware_concurrency": (4, 8),
        "max_touch_points": (5, 10),
        "screen": {
            "width": (768, 1024),
            "height": (1024, 1366),
            "pixel_ratio": (2, 2.25)
        }
    }
}

# Define OS-Browser compatibility constraints
OS_BROWSER_CONSTRAINTS: Dict[OSFamily, Set[BrowserFamily]] = {
    OSFamily.WINDOWS: {BrowserFamily.CHROME, BrowserFamily.FIREFOX, BrowserFamily.EDGE},
    OSFamily.MACOS: {BrowserFamily.CHROME, BrowserFamily.FIREFOX, BrowserFamily.SAFARI},
    OSFamily.LINUX: {BrowserFamily.CHROME, BrowserFamily.FIREFOX},
    OSFamily.ANDROID: {BrowserFamily.CHROME, BrowserFamily.FIREFOX},
    OSFamily.IOS: {BrowserFamily.SAFARI}
}

def validate_config(config: Dict[str, Any]) -> List[str]:
    """
    Validate configuration against defined constraints
    
    Args:
        config: Configuration dictionary to validate
        
    Returns:
        List of validation error messages (empty if valid)
    """
    errors: List[str] = []
    
    # Validate device-OS-browser combination
    device = DeviceType(config.get("device", "desktop"))
    os_family = OSFamily(config.get("os"))
    browser_family = BrowserFamily(config.get("browser").name)
    
    if browser_family not in OS_BROWSER_CONSTRAINTS[os_family]:
        errors.append(f"Browser {browser_family.value} is not supported on {os_family.value}")
    
    # Validate hardware constraints
    hw_constraints = HARDWARE_CONSTRAINTS[device]
    
    if config.get("device_memory") not in hw_constraints["device_memory"]:
        errors.append("Invalid device memory for device type")
    
    if config.get("hardware_concurrency") not in hw_constraints["hardware_concurrency"]:
        errors.append("Invalid hardware concurrency for device type")
    
    if config.get("max_touch_points") not in hw_constraints["max_touch_points"]:
        errors.append("Invalid touch points for device type")
    
    # Validate screen constraints
    screen = config.get("screen", {})
    screen_constraints = hw_constraints["screen"]
    
    if not (screen_constraints["width"][0] <= screen.get("width", 0) <= screen_constraints["width"][1]):
        errors.append("Invalid screen width for device type")
    
    if not (screen_constraints["height"][0] <= screen.get("height", 0) <= screen_constraints["height"][1]):
        errors.append("Invalid screen height for device type")
    
    if screen.get("pixel_ratio") not in screen_constraints["pixel_ratio"]:
        errors.append("Invalid pixel ratio for device type")
    
    return errors

def generate_consistent_config(
    device_type: DeviceType,
    os_family: OSFamily,
    browser_family: Optional[BrowserFamily] = None
) -> Dict[str, Any]:
    """
    Generate a consistent configuration based on device type and OS
    
    Args:
        device_type: Type of device
        os_family: Operating system family
        browser_family: Optional browser family (auto-selected if None)
        
    Returns:
        Consistent configuration dictionary
    """
    import random
    
    # Auto-select browser if not specified
    if browser_family is None:
        compatible_browsers = OS_BROWSER_CONSTRAINTS[os_family]
        browser_family = random.choice(list(compatible_browsers))
    
    # Get hardware constraints for device type
    hw_constraints = HARDWARE_CONSTRAINTS[device_type]
    
    # Generate consistent configuration
    config = {
        "device": device_type.value,
        "os": os_family.value,
        "browser": browser_family.value,
        "device_memory": random.choice(hw_constraints["device_memory"]),
        "hardware_concurrency": random.choice(hw_constraints["hardware_concurrency"]),
        "max_touch_points": random.choice(hw_constraints["max_touch_points"]),
        "screen": {
            "width": random.randint(*hw_constraints["screen"]["width"]),
            "height": random.randint(*hw_constraints["screen"]["height"]),
            "pixel_ratio": random.choice(hw_constraints["screen"]["pixel_ratio"])
        }
    }
    
    return config
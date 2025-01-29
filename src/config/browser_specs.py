from typing import Dict, List, Union, Tuple, Any
from enum import Enum
from browserforge.headers import Browser

class BrowserFamily(str, Enum):
    CHROME = "chrome"
    FIREFOX = "firefox" 
    SAFARI = "safari"
    EDGE = "edge"

# Realistic browser specifications based on common configurations
BROWSER_SPECIFICATIONS: Dict[str, Dict[str, Any]] = {
    "chrome": {
        "min_version": 100,
        "max_version": 122,
        "http_version": 2
    },
    "firefox": {
        "min_version": 85,
        "max_version": 115,
        "http_version": 2
    }
}

def create_browser_specs() -> List[Browser]:
    """
    Tạo danh sách các đặc tả browser chi tiết sử dụng Browserforge Browser class
    """
    browser_specs = []
    
    for browser_name, specs in BROWSER_SPECIFICATIONS.items():
        browser = Browser(
            name=browser_name,
            min_version=specs["min_version"],
            max_version=specs["max_version"],
            http_version=specs["http_version"]
        )
        browser_specs.append(browser)
    
    return browser_specs

def get_hardware_constraints(browser_name: str) -> Dict[str, Tuple[int, int]]:
    """
    Lấy các ràng buộc về phần cứng cho browser cụ thể
    """
    specs = BROWSER_SPECIFICATIONS[browser_name]
    return {
        "memory": specs["memory_range"],
        "cores": specs["cores_range"]
    } 
from enum import Enum
from typing import Dict, List, Tuple, Any, Optional, Union
from dataclasses import dataclass
from browserforge.headers import Browser, HeaderGenerator

@dataclass
class HeaderRule:
    name: str
    value: Union[str, List[str]]
    weight: float = 1.0  # Frequency weight
    required: bool = True
    conditions: Dict[str, Any] = None

class HeaderRuleManager:
    """Manages custom header generation rules with browser-specific configurations"""
    
    # Common security headers
    SECURITY_HEADERS = {
        "Sec-Fetch-Dest": ["document", "empty", "image"],
        "Sec-Fetch-Mode": ["navigate", "cors", "no-cors"],
        "Sec-Fetch-Site": ["same-origin", "cross-site", "same-site"],
        "Sec-Fetch-User": ["?1"],
    }
    
    # Browser-specific header rules
    BROWSER_HEADERS: Dict[str, Dict[str, HeaderRule]] = {
        "firefox": {
            "Accept": HeaderRule(
                name="Accept",
                value=["text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"],
                required=True,
                conditions={"version_min": 100}
            ),
            "Accept-Language": HeaderRule(
                name="Accept-Language",
                value=["en-US,en;q=0.5"],
                required=True
            ),
            "DNT": HeaderRule(
                name="DNT",
                value=["1"],
                weight=0.7,  # 70% of Firefox users enable DNT
                required=False
            ),
            "Upgrade-Insecure-Requests": HeaderRule(
                name="Upgrade-Insecure-Requests",
                value=["1"],
                required=True
            ),
            "Connection": HeaderRule(
                name="Connection",
                value=["keep-alive"],
                required=True
            )
        },
        "chrome": {
            "Accept": HeaderRule(
                name="Accept",
                value=["text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8"],
                required=True,
                conditions={"version_min": 100}
            ),
            "Accept-Language": HeaderRule(
                name="Accept-Language",
                value=["en-US,en;q=0.9"],
                required=True
            ),
            "sec-ch-ua": HeaderRule(
                name="sec-ch-ua",
                value=['".Not/A)Brand";v="99", "Google Chrome";v="103", "Chromium";v="103"'],
                required=True,
                conditions={"version_min": 90}
            )
        }
    }

    def __init__(self):
        self.header_generator = HeaderGenerator()

    def _get_browser_rules(self, browser: str, version: int) -> List[HeaderRule]:
        """Get applicable header rules for browser and version"""
        rules = []
        browser_rules = self.BROWSER_HEADERS.get(browser, {})
        
        for rule in browser_rules.values():
            if rule.conditions:
                min_version = rule.conditions.get("version_min", 0)
                max_version = rule.conditions.get("version_max", float("inf"))
                
                if min_version <= version <= max_version:
                    rules.append(rule)
            else:
                rules.append(rule)
                
        return rules

    def _apply_security_headers(self, headers: Dict[str, str], browser: str) -> Dict[str, str]:
        """Apply security headers based on browser"""
        for name, values in self.SECURITY_HEADERS.items():
            if name not in headers:
                headers[name] = values[0]  # Use first value as default
        return headers

    def generate_headers(
        self,
        browser: Union[str, Browser],
        version: Optional[int] = None,
        include_security: bool = True
    ) -> Dict[str, str]:
        """Generate headers with custom rules"""
        try:
            # Get browser name and version
            if isinstance(browser, Browser):
                browser_name = browser.name
                version = version or browser.max_version
            else:
                browser_name = browser
                version = version or 100  # Default version if not specified
            
            # Get base headers from BrowserForge
            base_headers = self.header_generator.generate(
                browser=browser_name,
                strict=False
            )
            
            # Get applicable rules
            rules = self._get_browser_rules(browser_name, version)
            
            # Apply custom rules
            for rule in rules:
                if rule.required or (not rule.required and rule.weight >= 0.5):
                    if isinstance(rule.value, list):
                        base_headers[rule.name] = rule.value[0]
                    else:
                        base_headers[rule.name] = rule.value
            
            # Apply security headers if requested
            if include_security:
                base_headers = self._apply_security_headers(base_headers, browser_name)
            
            return base_headers
            
        except Exception as e:
            raise ValueError(f"Failed to generate headers: {str(e)}") 
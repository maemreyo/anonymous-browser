from enum import Enum
from typing import Dict, List, Tuple, Any, Optional, Union
from dataclasses import dataclass
from browserforge.headers import Browser, HeaderGenerator
from .browser_specs import BrowserFamily
import logging

logger = logging.getLogger(__name__)

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
        self.base_headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Pragma': 'no-cache',
            'Cache-Control': 'no-cache'
        }

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

    def generate_headers(self, browser: BrowserFamily, version: Optional[int] = None) -> Dict[str, str]:
        """Generate headers based on browser and version"""
        try:
            base_headers = self.base_headers.copy()
            
            # Generate User-Agent based on browser family
            if browser == BrowserFamily.FIREFOX:
                user_agent = f"Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:{version}.0) Gecko/20100101 Firefox/{version}.0"
                base_headers.update({
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                    'TE': 'trailers'
                })
            
            elif browser == BrowserFamily.CHROME:
                user_agent = f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{version}.0.0.0 Safari/537.36"
                base_headers.update({
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                    'sec-ch-ua': f'"Chromium";v="{version}", "Google Chrome";v="{version}"',
                    'sec-ch-ua-mobile': '?0',
                    'sec-ch-ua-platform': '"Windows"'
                })
            
            else:
                raise ValueError(f"Unsupported browser family: {browser}")

            # Set User-Agent
            base_headers['User-Agent'] = user_agent
            
            logger.debug(f"Generated headers for {browser.value} v{version}")
            return base_headers

        except Exception as e:
            logger.error(f"Failed to generate headers: {e}")
            raise ValueError(f"Failed to generate headers: {str(e)}")

    def _get_browser_version(self, browser: BrowserFamily, version: Optional[int] = None) -> int:
        """Get appropriate browser version"""
        default_versions = {
            BrowserFamily.FIREFOX: 115,
            BrowserFamily.CHROME: 120
        }
        return version or default_versions.get(browser, 115) 
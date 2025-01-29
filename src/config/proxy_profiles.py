from typing import Dict, Any, Optional
from dataclasses import dataclass
import random
import json
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

@dataclass
class ProxyConfig:
    server: str  # proxy server address (e.g., "proxy.example.com:8080")
    username: Optional[str] = None
    password: Optional[str] = None
    bypass: Optional[str] = None  # domains to bypass proxy

    def to_dict(self) -> Dict[str, Any]:
        config = {
            "server": self.server
        }
        if self.username and self.password:
            config.update({
                "username": self.username,
                "password": self.password
            })
        if self.bypass:
            config["bypass"] = self.bypass
        return config

class ProxyProfiles:
    """Manages proxy configurations with smart rotation"""
    
    def __init__(self):
        self.config_path = Path("config/proxy_profiles.json")
        self.proxies = self._load_proxies()
        
    def _load_proxies(self) -> Dict[str, Dict[str, Any]]:
        """Load proxy list from config file"""
        try:
            if self.config_path.exists():
                with open(self.config_path) as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load proxy profiles: {e}")
        return self._load_default_proxies()

    def _load_default_proxies(self) -> Dict[str, Dict[str, Any]]:
        """Load default proxy configurations"""
        return {
            "regions": {
                "US": {
                    "proxies": [
                        {"server": "us-proxy1.example.com:8080"},
                        {"server": "us-proxy2.example.com:8080"}
                    ],
                    "weight": 0.3
                },
                "EU": {
                    "proxies": [
                        {"server": "eu-proxy1.example.com:8080"},
                        {"server": "eu-proxy2.example.com:8080"}
                    ],
                    "weight": 0.3
                },
                "ASIA": {
                    "proxies": [
                        {"server": "asia-proxy1.example.com:8080"},
                        {"server": "asia-proxy2.example.com:8080"}
                    ],
                    "weight": 0.2
                }
            }
        }

    def get_random_proxy(self, region: Optional[str] = None) -> ProxyConfig:
        """Get random proxy configuration, optionally from specific region"""
        if region and region in self.proxies["regions"]:
            proxy_list = self.proxies["regions"][region]["proxies"]
        else:
            # Select random region based on weights
            weights = [r["weight"] for r in self.proxies["regions"].values()]
            region = random.choices(list(self.proxies["regions"].keys()), weights=weights)[0]
            proxy_list = self.proxies["regions"][region]["proxies"]

        proxy_data = random.choice(proxy_list)
        return ProxyConfig(**proxy_data) 
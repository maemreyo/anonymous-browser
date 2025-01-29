from typing import Dict, Any, Optional
from dataclasses import dataclass
import aiohttp
from enum import Enum
import logging
from proxyscrape import create_collector, get_collector
from aiohttp_socks import ProxyConnector
from ..utils.proxy_logger import ProxyLogger

logger = logging.getLogger(__name__)

class ProxyProtocol(Enum):
    HTTP = "http"
    HTTPS = "https"
    SOCKS4 = "socks4"
    SOCKS5 = "socks5"

@dataclass
class ProxyConfig:
    server: str
    protocol: ProxyProtocol
    username: Optional[str] = None
    password: Optional[str] = None
    region: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "server": self.server,
            "protocol": self.protocol.value,
            "username": self.username,
            "password": self.password,
            "region": self.region
        }

class ProxyManager:
    def __init__(self):
        self.current_proxy = None
        self.collector = self._get_or_create_collector()
        self.logger = ProxyLogger()
        logger.info("ProxyManager initialized")

    def _get_or_create_collector(self) -> Any:
        """Get existing collector or create new one"""
        try:
            # Try to get existing collector
            collector = get_collector('default')
            if collector:
                logger.info("Using existing collector")
                return collector
        except:
            pass

        try:
            # Create new collector with all protocols
            collector = create_collector(
                'default',
                ['http', 'https', 'socks4', 'socks5']
            )
            logger.info("Created new collector")
            return collector
        except Exception as e:
            logger.error(f"Failed to create collector: {e}")
            raise RuntimeError("Could not initialize proxy collector")

    async def get_working_proxy(self) -> Optional[ProxyConfig]:
        """Get a working proxy from collector"""
        max_attempts = 5
        for _ in range(max_attempts):
            try:
                proxy = self.collector.get_proxy()
                if proxy:
                    proxy_config = ProxyConfig(
                        server=f"{proxy.host}:{proxy.port}",
                        protocol=ProxyProtocol(proxy.type),
                        username=getattr(proxy, 'username', None),
                        password=getattr(proxy, 'password', None)
                    )
                    
                    if await self._validate_proxy(proxy_config):
                        self.current_proxy = proxy_config
                        logger.info(f"Found working proxy: {proxy_config.server} ({proxy_config.protocol.value})")
                        return proxy_config
                    
            except Exception as e:
                logger.debug(f"Failed to get/validate proxy: {e}")
                continue
                
        logger.warning("No working proxy found after maximum attempts")
        return None

    async def _validate_proxy(self, proxy: ProxyConfig) -> bool:
        """Validate if proxy is working"""
        try:
            connector = ProxyConnector.from_url(
                f"{proxy.protocol.value}://{proxy.server}"
            )
            
            async with aiohttp.ClientSession(connector=connector, timeout=10) as session:
                async with session.get('http://ip-api.com/json') as response:
                    if response.status == 200:
                        data = await response.json()
                        proxy.region = data.get('countryCode')
                        logger.info(f"Proxy validation successful - IP: {data.get('query')}, Region: {proxy.region}")
                        return True
                        
        except Exception as e:
            logger.debug(f"Proxy validation failed: {e}")
        return False

    def get_proxy_config(self) -> Optional[Dict[str, Any]]:
        """Get current proxy configuration for Playwright"""
        return self.current_proxy.to_dict() if self.current_proxy else None 
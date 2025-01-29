from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
import aiohttp
import asyncio
from datetime import datetime, timedelta
import json
from pathlib import Path
import logging
import random
from enum import Enum
import aiofiles
from aiohttp import ClientTimeout
from aiohttp_socks import ProxyConnector
import requests
from ..utils.request_handler import RequestHandler, RetryConfig, RateLimitConfig, TimeoutConfig

logger = logging.getLogger(__name__)

class ProxyProtocol(Enum):
    HTTP = "http"
    HTTPS = "https"
    SOCKS4 = "socks4"
    SOCKS5 = "socks5"

@dataclass
class ProxyStatus:
    last_check: datetime
    response_time: float  # in seconds
    success_count: int
    fail_count: int
    last_error: Optional[str] = None

@dataclass
class ProxyConfig:
    server: str
    protocol: ProxyProtocol
    username: Optional[str] = None
    password: Optional[str] = None
    status: Optional[ProxyStatus] = None
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
    """Smart proxy manager with validation and rotation"""
    
    def __init__(self):
        self.config_path = Path("config/proxies")
        self.config_path.mkdir(parents=True, exist_ok=True)
        
        self.proxies: Dict[str, ProxyConfig] = {}
        self.status_cache: Dict[str, ProxyStatus] = {}
        
        # Rate limiting settings
        self.rate_limits = {
            "requests_per_minute": 60,
            "request_count": 0,
            "last_reset": datetime.now()
        }
        
        # Validation settings
        self.validation_urls = [
            "http://ip-api.com/json",
            "https://api.ipify.org?format=json",
            "http://httpbin.org/ip"
        ]
        
        # Initialize request handler
        self.request_handler = RequestHandler(
            retry_config=RetryConfig(
                max_attempts=3,
                base_delay=1.0,
                max_delay=10.0
            ),
            rate_limit_config=RateLimitConfig(
                requests_per_minute=60,
                burst_size=10
            ),
            timeout_config=TimeoutConfig(
                connect=5.0,
                read=10.0,
                total=20.0
            )
        )
        
        # Extended proxy sources
        self.proxy_sources = {
            "free": [
                # Public proxy lists
                "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
                "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/proxy.txt",
                "https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list.txt",
                "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt",
                "https://raw.githubusercontent.com/hookzof/socks5_list/master/proxy.txt",
                "https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/json/proxies.json",
                
                # API endpoints
                "https://proxylist.geonode.com/api/proxy-list?limit=100&page=1&sort_by=lastChecked&sort_type=desc&protocols=http%2Chttps%2Csocks4%2Csocks5",
                "https://www.proxy-list.download/api/v1/get?type=http",
                "https://www.proxy-list.download/api/v1/get?type=https",
                "https://www.proxy-list.download/api/v1/get?type=socks4",
                "https://www.proxy-list.download/api/v1/get?type=socks5"
            ],
            "premium": {
                # Premium proxy services (requires API key)
                "brightdata": "https://brightdata.com/api/proxy",
                "oxylabs": "https://developers.oxylabs.io/proxy",
                "smartproxy": "https://api.smartproxy.com/v1",
                "webshare": "https://proxy.webshare.io/api",
                "proxyrack": "https://api.proxyrack.net/v1"
            }
        }
        
        # Load proxies immediately on initialization
        asyncio.create_task(self.initialize())  # Initialize asynchronously

    async def initialize(self) -> None:
        """Initialize proxy manager and load initial proxies"""
        try:
            await self.load_all_proxies()
            logger.info(f"Initialized ProxyManager with {len(self.proxies)} proxies")
        except Exception as e:
            logger.error(f"Failed to initialize ProxyManager: {e}")

    async def load_all_proxies(self) -> None:
        """Load proxies from all available sources"""
        try:
            # First try loading from cache
            if await self._load_from_cache():
                return

            # If cache empty or expired, load from sources
            await self.load_free_proxies()
            await self._load_premium_if_available()
            
            # Cache the results
            await self._save_to_cache()
            
            logger.info(f"Loaded {len(self.proxies)} proxies from all sources")
        except Exception as e:
            logger.error(f"Failed to load proxies: {e}")
            # Load defaults as fallback
            self._load_default_proxies()

    async def _load_from_cache(self) -> bool:
        """Load proxies from cache file"""
        cache_file = self.config_path / "proxy_cache.json"
        try:
            if cache_file.exists():
                cache_age = datetime.now() - datetime.fromtimestamp(cache_file.stat().st_mtime)
                if cache_age < timedelta(hours=1):  # Cache valid for 1 hour
                    async with aiofiles.open(cache_file, 'r') as f:
                        content = await f.read()
                        cache_data = json.loads(content)
                        for proxy_data in cache_data:
                            self.proxies[proxy_data["server"]] = ProxyConfig(**proxy_data)
                        logger.info(f"Loaded {len(self.proxies)} proxies from cache")
                        return True
        except Exception as e:
            logger.warning(f"Failed to load from cache: {e}")
        return False

    async def _save_to_cache(self) -> None:
        """Save working proxies to cache"""
        try:
            cache_file = self.config_path / "proxy_cache.json"
            cache_data = [proxy.to_dict() for proxy in self.proxies.values()]
            async with aiofiles.open(cache_file, 'w') as f:
                await f.write(json.dumps(cache_data, indent=2))
        except Exception as e:
            logger.warning(f"Failed to save to cache: {e}")

    def _load_default_proxies(self) -> None:
        """Load default proxy configurations"""
        default_proxies = {
            "US": [
                ("104.227.13.3:8080", ProxyProtocol.HTTP),
                ("104.227.13.4:8080", ProxyProtocol.HTTPS)
            ],
            "EU": [
                ("45.155.68.129:8080", ProxyProtocol.HTTP),
                ("45.155.68.130:8080", ProxyProtocol.SOCKS5)
            ],
            "ASIA": [
                ("103.133.222.1:8080", ProxyProtocol.HTTP),
                ("103.133.222.2:8080", ProxyProtocol.SOCKS4)
            ]
        }
        
        for region, proxy_list in default_proxies.items():
            for server, protocol in proxy_list:
                proxy = ProxyConfig(
                    server=server,
                    protocol=protocol,
                    region=region
                )
                self.proxies[proxy.server] = proxy
                
        logger.info(f"Loaded {len(self.proxies)} default proxies")

    async def load_free_proxies(self) -> None:
        """Load free proxies from multiple sources"""
        sources = [
            "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
            "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/proxy.txt",
            "https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list.txt"
        ]
        
        async with aiohttp.ClientSession() as session:
            for source in sources:
                try:
                    async with session.get(source, timeout=10) as response:
                        if response.status == 200:
                            content = await response.text()
                            self._parse_proxy_list(content)
                except Exception as e:
                    logger.warning(f"Failed to load proxies from {source}: {e}")

    def _parse_proxy_list(self, content: str) -> None:
        """Parse proxy list from various formats"""
        for line in content.splitlines():
            try:
                if ':' not in line:
                    continue
                    
                parts = line.strip().split(':')
                if len(parts) >= 2:
                    host, port = parts[0:2]
                    protocol = ProxyProtocol.HTTP
                    
                    # Try to detect protocol
                    if len(parts) > 2:
                        proto = parts[2].lower()
                        if proto in [p.value for p in ProxyProtocol]:
                            protocol = ProxyProtocol(proto)
                    
                    proxy = ProxyConfig(
                        server=f"{host}:{port}",
                        protocol=protocol
                    )
                    
                    self.proxies[proxy.server] = proxy
            except Exception as e:
                logger.debug(f"Failed to parse proxy line: {line}, error: {e}")

    async def validate_proxy(self, proxy: ProxyConfig) -> bool:
        """Validate proxy with retry handling"""
        return await self.request_handler.execute(
            self._validate_proxy_internal,
            proxy,
            retry_key=f"validate:{proxy.server}"
        )

    async def _validate_proxy_internal(self, proxy: ProxyConfig) -> bool:
        """Validate proxy with multiple checks"""
        start_time = datetime.now()
        
        try:
            # Create connector based on protocol
            if proxy.protocol in [ProxyProtocol.SOCKS4, ProxyProtocol.SOCKS5]:
                connector = ProxyConnector.from_url(
                    f"{proxy.protocol.value}://{proxy.server}"
                )
            else:
                connector = aiohttp.TCPConnector()

            async with aiohttp.ClientSession(connector=connector) as session:
                for url in self.validation_urls:
                    try:
                        proxy_url = f"{proxy.protocol.value}://{proxy.server}"
                        async with session.get(
                            url,
                            proxy=proxy_url,
                            timeout=ClientTimeout(total=10)
                        ) as response:
                            if response.status == 200:
                                data = await response.json()
                                
                                # Update proxy region if available
                                if 'country' in data:
                                    proxy.region = data['country']
                                
                                response_time = (datetime.now() - start_time).total_seconds()
                                
                                # Update status
                                if proxy.server in self.status_cache:
                                    status = self.status_cache[proxy.server]
                                    status.success_count += 1
                                else:
                                    status = ProxyStatus(
                                        last_check=datetime.now(),
                                        response_time=response_time,
                                        success_count=1,
                                        fail_count=0
                                    )
                                
                                self.status_cache[proxy.server] = status
                                return True
                                
                    except Exception as e:
                        continue

            raise Exception("All validation URLs failed")
            
        except Exception as e:
            # Update failure status
            if proxy.server in self.status_cache:
                status = self.status_cache[proxy.server]
                status.fail_count += 1
                status.last_error = str(e)
            else:
                self.status_cache[proxy.server] = ProxyStatus(
                    last_check=datetime.now(),
                    response_time=10,
                    success_count=0,
                    fail_count=1,
                    last_error=str(e)
                )
            return False

    async def get_working_proxy(self, region: Optional[str] = None, max_retries: int = 3) -> Optional[ProxyConfig]:
        """Get working proxy with retry logic"""
        retries = 0
        while retries < max_retries:
            # Check rate limits
            if self._check_rate_limit():
                await asyncio.sleep(1)
                continue
                
            # Get candidate proxies
            candidates = self._get_proxy_candidates(region)
            if not candidates:
                await self.load_free_proxies()
                candidates = self._get_proxy_candidates(region)
                
            if not candidates:
                return None
                
            # Try proxies until one works
            for proxy in candidates:
                if await self.validate_proxy(proxy):
                    self._update_rate_limit()
                    return proxy
                    
            retries += 1
            await asyncio.sleep(1)
            
        return None

    def _get_proxy_candidates(self, region: Optional[str] = None) -> List[ProxyConfig]:
        """Get proxy candidates sorted by reliability"""
        candidates = []
        
        for proxy in self.proxies.values():
            if region and proxy.region and proxy.region.lower() != region.lower():
                continue
                
            # Calculate score based on status
            score = 0
            if proxy.server in self.status_cache:
                status = self.status_cache[proxy.server]
                success_rate = status.success_count / (status.success_count + status.fail_count) if status.success_count > 0 else 0
                score = success_rate * (1 / (status.response_time + 1))
                
            candidates.append((proxy, score))
            
        # Sort by score
        candidates.sort(key=lambda x: x[1], reverse=True)
        return [c[0] for c in candidates]

    def _check_rate_limit(self) -> bool:
        """Check if rate limit is exceeded"""
        now = datetime.now()
        if (now - self.rate_limits["last_reset"]) > timedelta(minutes=1):
            self.rate_limits["request_count"] = 0
            self.rate_limits["last_reset"] = now
            
        return self.rate_limits["request_count"] >= self.rate_limits["requests_per_minute"]

    def _update_rate_limit(self) -> None:
        """Update rate limit counter"""
        self.rate_limits["request_count"] += 1

    def save_status(self) -> None:
        """Save proxy status to file"""
        try:
            status_data = {
                server: {
                    "last_check": status.last_check.isoformat(),
                    "response_time": status.response_time,
                    "success_count": status.success_count,
                    "fail_count": status.fail_count,
                    "last_error": status.last_error
                }
                for server, status in self.status_cache.items()
            }
            
            with open(self.config_path / "proxy_status.json", 'w') as f:
                json.dump(status_data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save proxy status: {e}")

    async def load_premium_proxies(self, service: str, api_key: str) -> None:
        """Load proxies from premium proxy services"""
        if service not in self.proxy_sources["premium"]:
            raise ValueError(f"Unknown proxy service: {service}")

        try:
            async with aiohttp.ClientSession() as session:
                headers = {"Authorization": f"Bearer {api_key}"}
                async with session.get(self.proxy_sources["premium"][service], headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        self._parse_premium_proxies(service, data)
        except Exception as e:
            logger.error(f"Failed to load premium proxies from {service}: {e}")

    def _parse_premium_proxies(self, service: str, data: Dict[str, Any]) -> None:
        """Parse proxies from premium services"""
        try:
            if service == "brightdata":
                # Parse Bright Data format
                for proxy in data["proxies"]:
                    self.proxies[proxy["host"]] = ProxyConfig(
                        server=f"{proxy['host']}:{proxy['port']}",
                        protocol=ProxyProtocol(proxy["protocol"]),
                        username=proxy.get("username"),
                        password=proxy.get("password"),
                        region=proxy.get("country")
                    )
            elif service == "oxylabs":
                # Parse Oxylabs format
                # ... similar parsing for other services ...
                pass
        except Exception as e:
            logger.error(f"Failed to parse {service} proxies: {e}")

    async def _load_premium_if_available(self) -> None:
        """Load proxies from premium sources if API keys are configured"""
        config_file = self.config_path / "proxy_services.json"
        if config_file.exists():
            try:
                with open(config_file) as f:
                    services = json.load(f)
                    for service, api_key in services.items():
                        await self.load_premium_proxies(service, api_key)
            except Exception as e:
                logger.error(f"Failed to load proxy services config: {e}") 
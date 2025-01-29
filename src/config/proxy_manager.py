from typing import Dict, Any, Optional, List, Set
from dataclasses import dataclass
import aiohttp
import logging
from enum import Enum
import json
from pathlib import Path
import random
from datetime import datetime, timedelta
from rich.console import Console
from rich.table import Table
import asyncio
import aiofiles

console = Console()
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
    last_checked: Optional[datetime] = None
    response_time: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "server": self.server,
            "protocol": self.protocol.value,
            "username": self.username,
            "password": self.password,
            "region": self.region,
            "last_checked": self.last_checked.isoformat() if self.last_checked else None,
            "response_time": self.response_time
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProxyConfig':
        return cls(
            server=data['server'],
            protocol=ProxyProtocol[data['protocol'].upper()],
            username=data.get('username'),
            password=data.get('password'),
            region=data.get('region'),
            last_checked=datetime.fromisoformat(data['last_checked']) if data.get('last_checked') else None,
            response_time=data.get('response_time')
        )

    def __str__(self) -> str:
        return f"{self.protocol.value}://{self.server}"

class ProxyManager:
    def __init__(self, proxy_file: str = "config/proxies.json", working_proxies_file: str = "config/working_proxies.json"):
        self.current_proxy = None
        self.proxy_file = Path(proxy_file)
        self.working_proxies_file = Path(working_proxies_file)
        self.proxies: List[ProxyConfig] = []
        self.working_proxies: List[ProxyConfig] = []
        self._load_proxies()
        self._load_working_proxies()
        self._display_proxy_status()

    def _load_proxies(self) -> None:
        """Load proxies from JSON file"""
        try:
            if not self.proxy_file.exists():
                console.print(f"[red]Error: Proxy file not found at {self.proxy_file}[/red]")
                return

            with open(self.proxy_file) as f:
                proxy_list = json.load(f)

            for proxy_data in proxy_list:
                try:
                    protocol = proxy_data['protocol'][0].upper()
                    if not hasattr(ProxyProtocol, protocol):
                        continue

                    proxy = ProxyConfig(
                        server=f"{proxy_data['ip']}:{proxy_data['port']}",
                        protocol=ProxyProtocol[protocol],
                        username=proxy_data.get('username'),
                        password=proxy_data.get('password')
                    )
                    self.proxies.append(proxy)
                except Exception as e:
                    logger.error(f"Failed to parse proxy: {proxy_data} - {e}")
                    continue

        except Exception as e:
            logger.error(f"Failed to load proxies: {e}")
            raise

    def _load_working_proxies(self) -> None:
        """Load working proxies from cache file"""
        try:
            if self.working_proxies_file.exists():
                with open(self.working_proxies_file) as f:
                    data = json.load(f)
                    self.working_proxies = [ProxyConfig.from_dict(p) for p in data]
                    # Remove expired proxies (older than 1 hour)
                    now = datetime.now()
                    self.working_proxies = [
                        p for p in self.working_proxies 
                        if p.last_checked and now - p.last_checked < timedelta(hours=1)
                    ]
        except Exception as e:
            logger.error(f"Failed to load working proxies: {e}")

    async def _save_working_proxies(self) -> None:
        """Save working proxies to cache file"""
        try:
            self.working_proxies_file.parent.mkdir(parents=True, exist_ok=True)
            async with aiofiles.open(self.working_proxies_file, 'w') as f:
                data = [p.to_dict() for p in self.working_proxies]
                await f.write(json.dumps(data, indent=2))
        except Exception as e:
            logger.error(f"Failed to save working proxies: {e}")

    async def _validate_proxy(self, proxy: ProxyConfig) -> bool:
        """Validate if proxy is working"""
        try:
            connector = aiohttp.TCPConnector(ssl=False)
            timeout = aiohttp.ClientTimeout(total=5)  # Reduced timeout
            
            async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
                start_time = datetime.now()
                async with session.get(
                    'http://example.com',
                    proxy=f"{proxy.protocol.value}://{proxy.server}",
                    proxy_auth=aiohttp.BasicAuth(proxy.username, proxy.password) if proxy.username else None
                ) as response:
                    if response.status == 200:
                        proxy.response_time = (datetime.now() - start_time).total_seconds() * 1000
                        proxy.last_checked = datetime.now()
                        return True
        except:
            pass
        return False

    async def _check_proxies_parallel(self, proxies: List[ProxyConfig], max_concurrent: int = 10) -> List[ProxyConfig]:
        """Check multiple proxies in parallel"""
        working = []
        tasks = []
        
        async def check_proxy(proxy):
            if await self._validate_proxy(proxy):
                working.append(proxy)
                console.print(f"[green]Found working proxy: {proxy} ({proxy.response_time:.0f}ms)[/green]")

        # Create chunks of proxies to check
        chunks = [proxies[i:i + max_concurrent] for i in range(0, len(proxies), max_concurrent)]
        
        for chunk in chunks:
            tasks = [check_proxy(proxy) for proxy in chunk]
            await asyncio.gather(*tasks)
            
        return working

    async def get_working_proxy(self) -> Optional[ProxyConfig]:
        """Get a working proxy"""
        # First check existing working proxies
        if self.working_proxies:
            self.working_proxies.sort(key=lambda p: p.response_time or float('inf'))
            for proxy in self.working_proxies[:3]:  # Try top 3 fastest
                if await self._validate_proxy(proxy):
                    self.current_proxy = proxy
                    return proxy
            
            # Remove non-working proxies
            self.working_proxies = []

        # Check new proxies in parallel
        console.print("[blue]Testing proxies in parallel...[/blue]")
        working_proxies = await self._check_proxies_parallel(self.proxies)
        
        if working_proxies:
            # Sort by response time
            working_proxies.sort(key=lambda p: p.response_time or float('inf'))
            self.working_proxies = working_proxies
            self.current_proxy = working_proxies[0]
            await self._save_working_proxies()
            self._display_proxy_status()
            return self.current_proxy

        console.print("[red]No working proxy found[/red]")
        return None

    def get_proxy_config(self) -> Optional[Dict[str, Any]]:
        """Get current proxy configuration for Playwright"""
        if self.current_proxy:
            return {
                "server": f"{self.current_proxy.protocol.value}://{self.current_proxy.server}",
                "username": self.current_proxy.username,
                "password": self.current_proxy.password
            }
        return None

    def _display_proxy_status(self) -> None:
        """Display proxy status"""
        table = Table(title="Proxy Status")
        table.add_column("Server")
        table.add_column("Protocol")
        table.add_column("Response Time (ms)")
        table.add_column("Last Checked")

        for proxy in self.working_proxies:
            table.add_row(
                proxy.server,
                proxy.protocol.value,
                f"{proxy.response_time:.0f}" if proxy.response_time else "N/A",
                proxy.last_checked.isoformat() if proxy.last_checked else "N/A"
            )

        console.print(table) 
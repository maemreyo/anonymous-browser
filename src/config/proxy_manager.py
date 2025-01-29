from typing import Dict, Any, Optional, List, Protocol
from dataclasses import dataclass
import aiohttp
import logging
from enum import Enum
import json
from pathlib import Path
import random
from datetime import datetime, timedelta
from abc import ABC, abstractmethod
import asyncio
from rich.console import Console
from rich.table import Table

console = Console()
logger = logging.getLogger(__name__)


class ProxyProtocol(Enum):
    HTTP = "http"
    HTTPS = "https"
    SOCKS4 = "socks4"
    SOCKS5 = "socks5"

    @classmethod
    def guess_from_port(cls, port: int) -> "ProxyProtocol":
        """Guess protocol from port number"""
        if port in [1080, 4145, 4153]:
            return cls.SOCKS5
        elif port in [1081, 4144]:
            return cls.SOCKS4
        elif port in [8080, 8888, 3128]:
            return cls.HTTP
        else:
            return cls.HTTP  # Default to HTTP


@dataclass
class ProxyConfig:
    server: str
    protocol: ProxyProtocol
    username: Optional[str] = ""
    password: Optional[str] = ""
    region: Optional[str] = ""
    last_checked: Optional[datetime] = None
    response_time: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "server": self.server,
            "protocol": self.protocol.value,
            "username": self.username,
            "password": self.password,
            "region": self.region,
            "last_checked": (
                self.last_checked.isoformat() if self.last_checked else None
            ),
            "response_time": self.response_time,
        }

    def __str__(self) -> str:
        return f"{self.protocol.value}://{self.server}"


class ProxyAdapter(ABC):
    """Base adapter for proxy data sources"""

    @abstractmethod
    def adapt(self, data: Dict[str, Any]) -> Optional[ProxyConfig]:
        """Convert source data to ProxyConfig"""
        pass


class StandardProxyAdapter(ProxyAdapter):
    """Adapter for standard proxy format with protocol list"""

    def adapt(self, data: Dict[str, Any]) -> Optional[ProxyConfig]:
        try:
            protocol = data.get("protocol", ["http"])[0].upper()
            return ProxyConfig(
                server=f"{data['ip']}:{data['port']}",
                protocol=ProxyProtocol[protocol],
                username=data.get("username", ""),
                password=data.get("password", ""),
            )
        except Exception as e:
            logger.error(f"Failed to adapt standard proxy: {e}")
            return None


class RawProxyAdapter(ProxyAdapter):
    """Adapter for raw proxy format with ip_address and port"""

    def adapt(self, data: Dict[str, Any]) -> Optional[ProxyConfig]:
        try:
            port = int(data["port"])
            protocol = ProxyProtocol.guess_from_port(port)
            return ProxyConfig(server=f"{data['ip_address']}:{port}", protocol=protocol)
        except Exception as e:
            logger.error(f"Failed to adapt raw proxy: {e}")
            return None


class WorkingProxyAdapter(ProxyAdapter):
    """Adapter for working proxies format"""

    def adapt(self, data: Dict[str, Any]) -> Optional[ProxyConfig]:
        try:
            return ProxyConfig(
                server=data["server"],
                protocol=ProxyProtocol[data["protocol"].upper()],
                username=data.get("username", ""),
                password=data.get("password", ""),
                region=data.get("region"),
                last_checked=(
                    datetime.fromisoformat(data["last_checked"])
                    if data.get("last_checked")
                    else None
                ),
                response_time=data.get("response_time"),
            )
        except Exception as e:
            logger.error(f"Failed to adapt working proxy: {e}")
            return None


class ProxyManager:
    def __init__(
        self,
        proxy_file: str = "config/proxies.json",
        raw_proxy_file: str = "config/raw_proxies.json",
        working_proxies_file: str = "config/working_proxies.json",
    ):
        self.proxy_file = Path(proxy_file)
        self.raw_proxy_file = Path(raw_proxy_file)
        self.working_proxies_file = Path(working_proxies_file)

        self.adapters = {
            "standard": StandardProxyAdapter(),
            "raw": RawProxyAdapter(),
            "working": WorkingProxyAdapter(),
        }

        self.proxies: List[ProxyConfig] = []
        self.working_proxies: List[ProxyConfig] = []
        self.current_proxy = None

        self._load_all_proxies()
        self._display_proxy_status()

    def _load_all_proxies(self) -> None:
        """Load proxies from all sources"""
        # Load raw proxies
        if self.raw_proxy_file.exists():
            console.print(
                f"[blue]Loading raw proxies from {self.raw_proxy_file}[/blue]"
            )
            raw_proxies = self._load_from_file(self.raw_proxy_file, "raw")
            self.proxies.extend(raw_proxies)
            console.print(f"[green]Loaded {len(raw_proxies)} raw proxies[/green]")

        # Load standard proxies
        if self.proxy_file.exists():
            console.print(
                f"[blue]Loading standard proxies from {self.proxy_file}[/blue]"
            )
            std_proxies = self._load_from_file(self.proxy_file, "standard")
            self.proxies.extend(std_proxies)
            console.print(f"[green]Loaded {len(std_proxies)} standard proxies[/green]")

        # Load working proxies
        if self.working_proxies_file.exists():
            console.print(
                f"[blue]Loading working proxies from {self.working_proxies_file}[/blue]"
            )
            working_proxies = self._load_from_file(self.working_proxies_file, "working")
            # Filter out expired proxies
            now = datetime.now()
            working_proxies = [
                p
                for p in working_proxies
                if p.last_checked and now - p.last_checked < timedelta(hours=1)
            ]
            self.working_proxies.extend(working_proxies)
            console.print(
                f"[green]Loaded {len(working_proxies)} working proxies[/green]"
            )

    def _load_from_file(self, file_path: Path, adapter_type: str) -> List[ProxyConfig]:
        """Load proxies from a file using specified adapter"""
        try:
            with open(file_path) as f:
                data = json.load(f)

            adapter = self.adapters[adapter_type]
            proxies = []

            for item in data:
                proxy = adapter.adapt(item)
                if proxy:
                    proxies.append(proxy)

            return proxies

        except Exception as e:
            logger.error(f"Failed to load proxies from {file_path}: {e}")
            return []

    def _display_proxy_status(self) -> None:
        """Display current proxy status"""
        table = Table(title="Proxy Status")
        table.add_column("Type", style="cyan")
        table.add_column("Protocol", style="magenta")
        table.add_column("Server", style="green")
        table.add_column("Response Time", style="yellow")
        table.add_column("Status", style="blue")

        # Add working proxies
        for proxy in self.working_proxies:
            response_time = (
                f"{proxy.response_time:.0f}ms" if proxy.response_time else "N/A"
            )
            status = "Current" if proxy == self.current_proxy else "Working"
            table.add_row(
                "Working", proxy.protocol.value, proxy.server, response_time, status
            )

        # Add untested proxies
        for proxy in self.proxies[:5]:  # Show only first 5 untested proxies
            table.add_row(
                "Untested", proxy.protocol.value, proxy.server, "N/A", "Pending"
            )

        console.print(table)

    async def get_working_proxy(self) -> Optional[ProxyConfig]:
        """Get a working proxy from the list"""
        if not self.proxies:
            logger.warning("No proxies available")
            return None

        # Try proxies in random order
        proxies = self.proxies.copy()
        random.shuffle(proxies)

        for proxy in proxies:
            try:
                if await self._validate_proxy(proxy):
                    self.current_proxy = proxy
                    logger.info(
                        f"Found working proxy: {proxy.server} ({proxy.protocol.value})"
                    )
                    return proxy
            except Exception as e:
                logger.debug(f"Failed to validate proxy {proxy.server}: {e}")
                continue

        logger.warning("No working proxy found")
        return None

    async def _validate_proxy(self, proxy: ProxyConfig) -> bool:
        """Validate if proxy is working"""
        try:
            connector = aiohttp.TCPConnector(ssl=False)
            timeout = aiohttp.ClientTimeout(total=10)

            async with aiohttp.ClientSession(
                connector=connector, timeout=timeout
            ) as session:
                start_time = datetime.now()
                async with session.get(
                    "http://example.com",
                    proxy=f"{proxy.protocol.value}://{proxy.server}",
                    proxy_auth=(
                        aiohttp.BasicAuth(proxy.username, proxy.password)
                        if proxy.username
                        else None
                    ),
                ) as response:
                    if response.status == 200:
                        proxy.response_time = (
                            datetime.now() - start_time
                        ).total_seconds() * 1000
                        proxy.last_checked = datetime.now()
                        return True

        except Exception as e:
            logger.debug(f"Proxy validation failed: {e}")
        return False

    def get_proxy_config(self) -> Optional[Dict[str, Any]]:
        """Get current proxy configuration for Playwright"""
        if self.current_proxy:
            return {
                "server": f"{self.current_proxy.protocol.value}://{self.current_proxy.server}",
                "username": self.current_proxy.username,
                "password": self.current_proxy.password,
            }
        return None

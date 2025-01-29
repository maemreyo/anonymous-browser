from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from datetime import datetime
import logging

console = Console()
logger = logging.getLogger(__name__)

class ProxyLogger:
    def __init__(self):
        self.console = Console()
        
    def log_proxy_status(self, proxy_config, ip_info=None):
        """Log proxy status in a formatted table"""
        table = Table(title="🌐 Proxy Configuration", show_header=True)
        
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="green")
        
        if proxy_config:
            table.add_row("Status", "✅ Connected")
            table.add_row("Server", proxy_config.get("server", "N/A"))
            table.add_row("Protocol", proxy_config.get("protocol", "N/A"))
            table.add_row("Region", proxy_config.get("region", "N/A"))
        else:
            table.add_row("Status", "❌ Not Connected")
            
        if ip_info:
            table.add_row("Current IP", ip_info.get("ip", "N/A"))
            table.add_row("Country", ip_info.get("country", "N/A"))
            table.add_row("City", ip_info.get("city", "N/A"))
            table.add_row("ISP", ip_info.get("isp", "N/A"))
            
        self.console.print(table)
        
    def log_proxy_change(self, old_proxy, new_proxy):
        """Log when proxy changes"""
        panel = Panel(
            f"Proxy Changed\nFrom: {old_proxy.server if old_proxy else 'None'}\nTo: {new_proxy.server if new_proxy else 'None'}",
            title="🔄 Proxy Rotation",
            style="yellow"
        )
        self.console.print(panel)
        
    def log_proxy_error(self, error_msg):
        """Log proxy errors"""
        panel = Panel(
            str(error_msg),
            title="❌ Proxy Error",
            style="red"
        )
        self.console.print(panel) 
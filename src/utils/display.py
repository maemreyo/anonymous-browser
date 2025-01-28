from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from typing import Dict, Any
from browserforge.fingerprints import Fingerprint
import json

console = Console()

def format_fingerprint_for_display(fingerprint: Fingerprint) -> Dict[str, Any]:
    """Convert Fingerprint object to both compact and detailed format"""
    navigator = fingerprint.navigator
    screen = fingerprint.screen
    
    return {
        # Compact display
        "compact": {
            "id": navigator.userAgent.split('/')[-2].split()[0][:3].upper(),
            "os": navigator.platform.split()[0],
            "hw": f"{navigator.hardwareConcurrency}C/{getattr(navigator, 'deviceMemory', 'N/A')}GB",
            "res": f"{screen.width}x{screen.height}@{screen.devicePixelRatio}x"
        },
        # Detailed display
        "detailed": {
            "Browser Info": {
                "User Agent": navigator.userAgent,
                "Platform": navigator.platform,
                "Language": getattr(navigator, 'language', 'N/A'),
                "Languages": ", ".join(getattr(navigator, 'languages', ['N/A']))
            },
            "Hardware": {
                "CPU Cores": str(navigator.hardwareConcurrency),
                "Memory": f"{getattr(navigator, 'deviceMemory', 'N/A')}GB",
                "Touch Points": str(getattr(navigator, 'maxTouchPoints', 0)),
                "Color Depth": f"{screen.colorDepth}bit"
            },
            "Screen": {
                "Resolution": f"{screen.width}x{screen.height}",
                "Pixel Ratio": str(screen.devicePixelRatio),
                "Available Size": f"{getattr(screen, 'availWidth', screen.width)}x{getattr(screen, 'availHeight', screen.height)}",
                "Color Depth": f"{screen.colorDepth}-bit"
            },
            "Additional": {
                "Timezone": getattr(navigator, 'timezone', 'N/A'),
                "Product": getattr(navigator, 'product', 'N/A'),
                "Vendor": getattr(navigator, 'vendor', 'N/A'),
                "Do Not Track": getattr(navigator, 'doNotTrack', 'N/A')
            }
        }
    }

def show_active_config(fingerprint: Fingerprint) -> None:
    """Display active configuration in a compact panel"""
    config = format_fingerprint_for_display(fingerprint)
    compact = config['compact']  # Get the compact section
    
    info = f"[bold white]{compact['id']}[/] | [cyan]{compact['os']}[/] | [green]{compact['hw']}[/] | [yellow]{compact['res']}[/]"
    console.print(Panel(info, title="[bold blue]Browser Config", border_style="blue"))

def get_js_config(fingerprint: Fingerprint) -> str:
    """Generate JavaScript-compatible configuration object"""
    config = format_fingerprint_for_display(fingerprint)
    return json.dumps(config) 
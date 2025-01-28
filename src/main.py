import sys
from pathlib import Path

# Thêm thư mục gốc vào PYTHONPATH
root_dir = Path(__file__).parent.parent
sys.path.append(str(root_dir))

from typing import Optional
import asyncio
from rich.console import Console

from src.core.browser_manager import AnonymousBrowser

console = Console()

async def main():
    browser: Optional[AnonymousBrowser] = None
    try:
        browser = AnonymousBrowser()
        await browser.launch()
        
        # Navigate and inject config display
        await browser.page.goto("https://example.com")
        await browser.inject_config_display()
        
        console.print("\n[bold green]Browser launched successfully!")
        console.print("[italic]The current configuration is visible in both terminal and browser")
        console.print("[italic]Move mouse over the bottom-right corner to see browser config")
        
        input("\nPress Enter to close the browser...")
    
    finally:
        if browser:
            await browser.close()


if __name__ == "__main__":
    asyncio.run(main())

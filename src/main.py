import sys
from pathlib import Path
import asyncio
from rich.console import Console
from typing import Optional
import time

from src.core.browser_manager import AnonymousBrowser
from src.core.network_handler import NetworkRequestHandler, RequestType

console = Console()

class NetworkTester:
    def __init__(self, browser: AnonymousBrowser):
        self.browser = browser
        self.network_handler = browser.network_handler  # Use browser's network handler
        
    async def setup_tests(self):
        """Setup network testing environment"""
        # Add test request filter
        self.network_handler.add_request_filter(
            r".*\.(png|jpg|jpeg|gif)$",
            self._log_image_request
        )
        
        console.print("[bold green]Network testing setup complete![/]")
    
    def _log_image_request(self, request) -> None:
        """Log image requests for testing"""
        console.print(f"[yellow]Image request detected:[/] {request.url}")
        return None

async def main():
    browser: Optional[AnonymousBrowser] = None
    try:
        browser = AnonymousBrowser()
        await browser.launch()  # This is now properly awaited
        
        # Initialize network tester
        tester = NetworkTester(browser)
        await tester.setup_tests()
        
        console.print("\n[bold green]Browser launched with network testing enabled!")
        console.print("[italic]Testing sites will be loaded automatically...")
        
        # Test case 1: Regular website
        console.print("\n[bold]Test Case 1:[/] Loading regular website")
        await browser.page.goto("https://example.com")
        await asyncio.sleep(2)
        
        # Interactive testing mode
        console.print("\n[bold green]Entering interactive testing mode[/]")
        console.print("Press Ctrl+C to exit...")
        
        while True:
            await asyncio.sleep(1)
    
    except KeyboardInterrupt:
        console.print("\n[yellow]Exiting network testing mode...[/]")
    
    except Exception as e:
        console.print(f"\n[bold red]Error:[/] {str(e)}")
        raise  # Add this to see full traceback
    
    finally:
        if browser:
            await browser.close()
            console.print("[bold green]Browser closed successfully![/]")

if __name__ == "__main__":
    asyncio.run(main())

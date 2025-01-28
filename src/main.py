import sys
from pathlib import Path

# Thêm thư mục gốc vào PYTHONPATH
root_dir = Path(__file__).parent.parent
sys.path.append(str(root_dir))

from typing import Optional
import asyncio

from src.core.browser_manager import AnonymousBrowser


async def main():
    # Create browser instance (using latest version)
    browser: Optional[AnonymousBrowser] = None
    try:
        browser = AnonymousBrowser()
        await browser.launch()

        # Navigate to a website
        await browser.page.goto("https://example.com")

        # Wait for user input before closing
        input("Press Enter to close the browser...")

    finally:
        # Ensure browser is properly closed even if an error occurs
        if browser:
            await browser.close()


if __name__ == "__main__":
    asyncio.run(main())

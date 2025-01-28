from typing import Optional, Dict, Any
from playwright.async_api import async_playwright, Browser, Page
from browserforge.injectors.playwright import AsyncNewContext
from .fingerprint_generator import AnonymousFingerprint
from ..utils.logger import setup_logger

logger = setup_logger(__name__)

class AnonymousBrowser:
    def __init__(self) -> None:
        self.fingerprint_generator = AnonymousFingerprint()
        self.browser: Optional[Browser] = None
        self.context = None
        self.page: Optional[Page] = None
    
    async def launch(self) -> None:
        """Launch a new browser instance with random fingerprint"""
        try:
            config = self.fingerprint_generator.generate()
            playwright = await async_playwright().start()
            
            self.browser = await playwright.chromium.launch(
                headless=False
            )
            
            # Create a new context with the injected fingerprint
            self.context = await AsyncNewContext(
                self.browser,
                fingerprint=config["fingerprint"]
            )
            
            self.page = await self.context.new_page()
            logger.info("Browser launched successfully with new fingerprint")
            
        except Exception as e:
            logger.error(f"Failed to launch browser: {str(e)}")
            raise
    
    async def close(self) -> None:
        """Close all browser resources"""
        if self.page:
            await self.page.close()
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close() 
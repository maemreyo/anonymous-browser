import pytest
from src.core.browser_manager import AnonymousBrowser

class TestAnonymousBrowser:
    @pytest.fixture
    async def browser(self):
        browser = AnonymousBrowser()
        yield browser
        await browser.close()

    @pytest.mark.asyncio
    async def test_browser_launch(self, browser):
        """Test browser launch with fingerprint injection"""
        await browser.launch()
        
        assert browser.browser is not None
        assert browser.context is not None
        assert browser.page is not None

    @pytest.mark.asyncio
    async def test_browser_navigation(self, browser):
        """Test browser navigation capabilities"""
        await browser.launch()
        await browser.page.goto("https://example.com")
        
        assert "Example Domain" in await browser.page.title()

    @pytest.mark.asyncio
    async def test_browser_cleanup(self, browser):
        """Test proper browser cleanup"""
        await browser.launch()
        await browser.close()
        
        assert browser.page is None or browser.page.is_closed()
        assert browser.context is None
        assert browser.browser is None 
import pytest

from src.core.browser_manager import AnonymousBrowser


class TestAnonymousBrowser:
    @pytest.fixture
    async def browser(self):
        browser = AnonymousBrowser()
        try:
            await browser.launch()
            yield browser
        finally:
            await browser.close()

    @pytest.mark.asyncio
    async def test_browser_launch(self):
        """Test browser launch with fingerprint injection"""
        browser = AnonymousBrowser()
        await browser.launch()
        
        try:
            assert browser.browser is not None
            assert browser.context is not None
            assert browser.page is not None
        finally:
            await browser.close()

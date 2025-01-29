import pytest
import asyncio
from playwright.async_api import async_playwright
from src.core.context_spoofer import ContextSpoofer, SpooferType
from src.core.browser_manager import AnonymousBrowser
import logging
import json
from datetime import datetime
import pytz

logger = logging.getLogger(__name__)

class TestContextSpoofer:
    @pytest.fixture
    async def browser(self):
        """Setup test browser instance"""
        browser = AnonymousBrowser()
        await browser.launch()
        try:
            yield browser
        finally:
            await browser.close()

    @pytest.fixture(autouse=True)
    def event_loop(self):
        """Create event loop for each test"""
        loop = asyncio.get_event_loop()
        yield loop
        
    async def _get_browser_from_fixture(self, browser_fixture):
        """Helper to get browser instance from fixture"""
        async for browser in browser_fixture:
            return browser
        return None

    @pytest.mark.asyncio
    async def test_timezone_spoofing(self, browser):
        """Test timezone spoofing functionality"""
        browser_instance = await self._get_browser_from_fixture(browser)
        assert browser_instance is not None
        
        # Configure timezone spoof
        browser_instance.context_spoofer.configure_spoof("timezone", {
            "enabled": True,
            "timezone_id": "Asia/Tokyo",
            "locale": "ja-JP"
        })

        # Navigate to a test page
        await browser_instance.page.goto("about:blank")
        
        # Test timezone with simpler check
        timezone_check = await browser_instance.page.evaluate("""
            () => {
                const formatter = new Intl.DateTimeFormat();
                return {
                    timezone: formatter.resolvedOptions().timeZone,
                    locale: navigator.language
                };
            }
        """)
        
        assert timezone_check["timezone"] == "Asia/Tokyo"
        logger.info(f"Timezone check passed: {json.dumps(timezone_check, indent=2)}")

    @pytest.mark.asyncio
    async def test_audio_spoofing(self, browser):
        """Test audio context spoofing"""
        browser_instance = await self._get_browser_from_fixture(browser)
        assert browser_instance is not None
        
        # Configure audio spoof
        browser_instance.context_spoofer.configure_spoof("audio", {
            "enabled": True,
            "sample_rate": 48000,
            "channel_count": 2
        })

        # Test audio context
        audio_check = await browser_instance.page.evaluate("""
            () => {
                const audioContext = new AudioContext();
                return {
                    sampleRate: audioContext.sampleRate,
                    channelCount: audioContext.destination.channelCount,
                    state: audioContext.state
                }
            }
        """)
        
        assert audio_check["sampleRate"] == 48000
        assert audio_check["channelCount"] == 2
        logger.info(f"Audio check passed: {json.dumps(audio_check, indent=2)}")

    @pytest.mark.asyncio
    async def test_timezone_validation(self):
        """Test timezone validation"""
        spoofer = ContextSpoofer()
        
        # Test valid timezone
        spoofer.configure_spoof("timezone", {
            "timezone_id": "Europe/London"
        })
        
        # Test invalid timezone
        with pytest.raises(ValueError):
            spoofer.configure_spoof("timezone", {
                "timezone_id": "Invalid/Timezone"
            })

    @pytest.mark.asyncio
    async def test_real_world_scenario(self, browser):
        """Test spoofing in real-world scenario"""
        browser_instance = await self._get_browser_from_fixture(browser)
        assert browser_instance is not None
        
        # Configure spoofs
        browser_instance.context_spoofer.configure_spoof("timezone", {
            "enabled": True,
            "timezone_id": "Europe/Paris",
            "locale": "fr-FR"
        })
        
        browser_instance.context_spoofer.configure_spoof("audio", {
            "enabled": True,
            "sample_rate": 44100,
            "channel_count": 2,
            "noise_value": 0.01
        })

        await browser_instance.page.goto("about:blank")
        
        # Test with simpler checks
        timezone_info = await browser_instance.page.evaluate("""
            () => {
                const formatter = new Intl.DateTimeFormat();
                return {
                    timezone: formatter.resolvedOptions().timeZone,
                    locale: navigator.language
                };
            }
        """)
        
        audio_info = await browser_instance.page.evaluate("""
            () => {
                const ctx = new AudioContext();
                return {
                    sampleRate: ctx.sampleRate,
                    channelCount: ctx.destination.channelCount
                };
            }
        """)
        
        assert timezone_info["timezone"] == "Europe/Paris"
        assert audio_info["sampleRate"] == 44100
        
        logger.info(f"Timezone check: {json.dumps(timezone_info, indent=2)}")
        logger.info(f"Audio check: {json.dumps(audio_info, indent=2)}")

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for pytest-asyncio"""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
    yield loop
    loop.close() 
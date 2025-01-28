from typing import Optional, Dict, Any
from playwright.async_api import async_playwright, Browser, Page
from browserforge.injectors.playwright import AsyncNewContext
from .fingerprint_generator import AnonymousFingerprint
from ..utils.logger import setup_logger
from ..utils.display import show_active_config, get_js_config
from rich.console import Console

console = Console()
logger = setup_logger(__name__)


class AnonymousBrowser:
    def __init__(self) -> None:
        self.fingerprint_generator = AnonymousFingerprint()
        self.browser: Optional[Browser] = None
        self.context = None
        self.page: Optional[Page] = None
        self.current_config: Optional[Dict[str, Any]] = None

    async def launch(self) -> None:
        """Launch a new browser instance with random fingerprint"""
        try:
            config = self.fingerprint_generator.generate()
            self.current_config = config["fingerprint"]  # Đây là đối tượng Fingerprint

            # Display configuration
            console.print("\n[bold yellow]Launching browser with configuration:[/]")
            show_active_config(self.current_config)

            playwright = await async_playwright().start()

            self.browser = await playwright.chromium.launch(headless=False)

            # Create a new context with the injected fingerprint
            self.context = await AsyncNewContext(
                self.browser, fingerprint=self.current_config
            )

            self.page = await self.context.new_page()
            logger.info("Browser launched successfully with new fingerprint")

        except Exception as e:
            logger.error(f"Failed to launch browser: {str(e)}")
            raise

    async def inject_config_display(self) -> None:
        """Inject configuration display with all info and toggle button"""
        if self.page and self.current_config:
            js_code = """
            const configDiv = document.createElement('div');
            configDiv.id = 'browser-config';
            
            const styles = document.createElement('style');
            styles.textContent = `
                #browser-config {
                    position: fixed;
                    top: 10px;
                    right: 10px;
                    font-family: monospace;
                    font-size: 11px;
                    z-index: 9999;
                    user-select: none;
                    background: #000;
                    color: #fff;
                    border-radius: 3px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.3);
                    opacity: 0.85;
                    padding: 4px 8px;
                    width: max-content;
                }
                .config-section {
                    margin: 4px 0;
                    padding: 2px 0;
                    background: #000;
                }
                .config-section:last-child {
                }
                .config-row {
                    display: block;
                    line-height: 15px;
                    white-space: nowrap;
                    margin: 8px auto;
                    padding: 8px 16px;
                    background-color: #000;
                }
                .config-label {
                    color: #888;
                    display: inline-block;
                    min-width: 20px;
                }
                .config-separator {
                    color: #888;
                    margin: 0 4px;
                }
                .config-value {
                    color: #2196F3;
                }
                .config-value.os { color: #2196F3; }
                .config-value.hw { color: #FFC107; }
                .config-value.screen { color: #E91E63; }
                #toggle-button {
                    position: fixed;
                    top: 10px;
                    right: 10px;
                    background: #000;
                    color: #4CAF50;
                    border: none;
                    border-radius: 3px;
                    padding: 3px 6px;
                    cursor: pointer;
                    font-family: monospace;
                    font-size: 11px;
                    opacity: 0.85;
                    display: none;
                    z-index: 9999;
                }
                #config-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-top: 8px;
                    margin-bottom: 4px;
                    padding-bottom: 2px;
                    background: #000;
                }
                #minimize-button {
                    color: #888;
                    cursor: pointer;
                    padding: 0 4px;
                }
                .hidden {
                    display: none !important;
                }
            `;
            document.head.appendChild(styles);
            
            const config = %s;
            
            // Main config view with all information
            configDiv.innerHTML = `
                <div id="config-header">
                    <span>
                        <span style="color:#4CAF50">${config.compact.id}</span>
                        <span class="config-value os">${config.compact.os}</span>
                        <span class="config-value hw">${config.compact.hw}</span>
                        <span class="config-value screen">${config.compact.res}</span>
                    </span>
                    <span id="minimize-button">▼</span>
                </div>
                ${Object.entries(config.detailed).map(([section, items]) => `
                    <div class="config-section">
                        ${Object.entries(items).map(([label, value]) => `
                            <div class="config-row">
                                <span class="config-label">${label}</span>
                                <span class="config-separator">:</span>
                                <span class="config-value">${value}</span>
                            </div>
                        `).join('')}
                    </div>
                `).join('')}
            `;
            
            // Create toggle button (initially hidden)
            const toggleButton = document.createElement('button');
            toggleButton.id = 'toggle-button';
            toggleButton.textContent = '▲ Show';
            toggleButton.style.display = 'none';
            document.body.appendChild(toggleButton);
            
            // Add toggle functionality
            const minimizeButton = configDiv.querySelector('#minimize-button');
            let isMinimized = false;
            
            function toggleView() {
                isMinimized = !isMinimized;
                if (isMinimized) {
                    configDiv.classList.add('hidden');
                    toggleButton.style.display = 'block';
                    toggleButton.textContent = '▲ Show';
                } else {
                    configDiv.classList.remove('hidden');
                    toggleButton.style.display = 'none';
                    minimizeButton.textContent = '▼';
                }
            }
            
            minimizeButton.onclick = toggleView;
            toggleButton.onclick = toggleView;
            
            document.body.appendChild(configDiv);
            """ % get_js_config(
                self.current_config
            )

            await self.page.evaluate(js_code)
        else:
            logger.warning("Cannot inject config display: page or config not available")

    async def close(self) -> None:
        """Close all browser resources"""
        if self.page:
            await self.page.close()
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
            await self.browser.close()

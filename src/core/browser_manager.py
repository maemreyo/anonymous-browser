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
            
            self.browser = await playwright.chromium.launch(
                headless=False
            )
            
            # Create a new context with the injected fingerprint
            self.context = await AsyncNewContext(
                self.browser,
                fingerprint=self.current_config
            )
            
            self.page = await self.context.new_page()
            logger.info("Browser launched successfully with new fingerprint")
            
        except Exception as e:
            logger.error(f"Failed to launch browser: {str(e)}")
            raise
    
    async def inject_config_display(self) -> None:
        """Inject configuration display with expandable details into webpage"""
        if self.page and self.current_config:
            js_code = """
            const configDiv = document.createElement('div');
            configDiv.id = 'browser-config';
            
            // Styles
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
                }
                #config-compact {
                    background: #000;
                    color: #fff;
                    padding: 5px 8px;
                    border-radius: 3px;
                    cursor: pointer;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.3);
                    opacity: 0.8;
                }
                #config-detailed {
                    display: none;
                    background: #1a1a1a;
                    color: #fff;
                    padding: 10px;
                    border-radius: 3px;
                    margin-top: 5px;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.5);
                    width: 300px;
                }
                .config-section {
                    margin-bottom: 10px;
                }
                .config-section-title {
                    color: #4CAF50;
                    font-weight: bold;
                    margin-bottom: 5px;
                    border-bottom: 1px solid #333;
                }
                .config-row {
                    display: flex;
                    justify-content: space-between;
                    margin: 2px 0;
                }
                .config-label {
                    color: #888;
                }
                .config-value {
                    color: #2196F3;
                }
                #toggle-arrow {
                    margin-left: 8px;
                    transition: transform 0.3s;
                }
                .arrow-up {
                    transform: rotate(180deg);
                }
            `;
            document.head.appendChild(styles);
            
            const config = %s;
            
            // Compact view
            const compactView = document.createElement('div');
            compactView.id = 'config-compact';
            compactView.innerHTML = `
                <span style="color:#4CAF50">${config.compact.id}</span>
                <span style="color:#888">|</span>
                <span style="color:#2196F3">${config.compact.os}</span>
                <span style="color:#888">|</span>
                <span style="color:#FFC107">${config.compact.hw}</span>
                <span style="color:#888">|</span>
                <span style="color:#E91E63">${config.compact.res}</span>
                <span id="toggle-arrow">▼</span>
            `;
            
            // Detailed view
            const detailedView = document.createElement('div');
            detailedView.id = 'config-detailed';
            
            // Generate detailed sections
            Object.entries(config.detailed).forEach(([section, items]) => {
                const sectionEl = document.createElement('div');
                sectionEl.className = 'config-section';
                sectionEl.innerHTML = `
                    <div class="config-section-title">${section}</div>
                    ${Object.entries(items).map(([label, value]) => `
                        <div class="config-row">
                            <span class="config-label">${label}:</span>
                            <span class="config-value">${value}</span>
                        </div>
                    `).join('')}
                `;
                detailedView.appendChild(sectionEl);
            });
            
            configDiv.appendChild(compactView);
            configDiv.appendChild(detailedView);
            
            // Toggle detailed view
            let isExpanded = false;
            compactView.onclick = () => {
                isExpanded = !isExpanded;
                detailedView.style.display = isExpanded ? 'block' : 'none';
                document.getElementById('toggle-arrow').classList.toggle('arrow-up');
            };
            
            document.body.appendChild(configDiv);
            """ % get_js_config(self.current_config)
            
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
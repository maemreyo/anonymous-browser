import asyncio
from rich.console import Console
from rich.table import Table
from src.core.browser_manager import AnonymousBrowser
import json

console = Console()

async def interactive_test():
    browser = None
    try:
        browser = AnonymousBrowser()
        await browser.launch()
        
        # Create test table
        table = Table(title="Spoofing Test Results")
        table.add_column("Test", style="cyan")
        table.add_column("Result", style="green")
        
        # Test timezone
        console.print("\n[bold]Testing Timezone Spoofing...[/]")
        timezone_result = await browser.page.evaluate("""
            () => {
                return {
                    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
                    date: new Date().toLocaleString(),
                    offset: new Date().getTimezoneOffset()
                }
            }
        """)
        table.add_row("Timezone", json.dumps(timezone_result, indent=2))
        
        # Test audio
        console.print("\n[bold]Testing Audio Context...[/]")
        audio_result = await browser.page.evaluate("""
            () => {
                const ctx = new AudioContext();
                return {
                    sampleRate: ctx.sampleRate,
                    channelCount: ctx.destination.channelCount,
                    state: ctx.state
                }
            }
        """)
        table.add_row("Audio", json.dumps(audio_result, indent=2))
        
        # Display results
        console.print(table)
        
        # Interactive testing
        console.print("\n[bold green]Starting interactive test mode[/]")
        console.print("Browser is open for manual testing. Press Ctrl+C to exit.")
        
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        console.print("\n[yellow]Exiting test mode...[/]")
        
    finally:
        if browser:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(interactive_test()) 
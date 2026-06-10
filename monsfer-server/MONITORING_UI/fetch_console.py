import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        # Create a context with cookies if needed, or just let auto-login handle it
        context = await browser.new_context()
        page = await context.new_page()
        
        # Capture console logs
        page.on("console", lambda msg: print(f"[CONSOLE] {msg.type}: {msg.text}"))
        page.on("pageerror", lambda err: print(f"[PAGE ERROR] {err}"))
        
        # Capture network requests/responses
        def handle_response(response):
            if "api" in response.url:
                print(f"[API RESPONSE] {response.url} -> {response.status}")
                try:
                    # print response body
                    asyncio.create_task(print_body(response))
                except Exception:
                    pass
                    
        async def print_body(resp):
            try:
                text = await resp.text()
                print(f"[API BODY] {resp.url} -> {text[:500]}")
            except Exception:
                pass
                
        page.on("response", handle_response)
        
        print("Navigating to WiFi page...")
        await page.goto("http://127.0.0.1:5105/wifi")
        await page.wait_for_timeout(3000)
        
        print("Clicking refresh button...")
        await page.click("#wifiScanBtn")
        await page.wait_for_timeout(3000)
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())

from playwright.sync_api import sync_playwright
import time
import os

CDP_PORT = 9222
SCREENSHOT_PATH = r"C:\Users\ashus\SaudiaAutomation\screenshots\debug_gmail_browser.png"
os.makedirs(os.path.dirname(SCREENSHOT_PATH), exist_ok=True)

print("Connecting to Brave via CDP...")
with sync_playwright() as p:
    try:
        browser = p.chromium.connect_over_cdp(f"http://localhost:{CDP_PORT}")
        context = browser.contexts[0] if browser.contexts else browser.new_context()
        page = context.new_page()
        
        print("Navigating to Gmail...")
        page.goto("https://mail.google.com", timeout=30000)
        time.sleep(5)
        
        print(f"Current URL: {page.url}")
        print(f"Title: {page.title()}")
        
        # Take screenshot
        page.screenshot(path=SCREENSHOT_PATH)
        print(f"Screenshot saved to {SCREENSHOT_PATH}")
        
        page.close()
    except Exception as e:
        print(f"Error: {e}")

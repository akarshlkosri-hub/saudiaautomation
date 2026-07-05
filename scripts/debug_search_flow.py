from playwright.sync_api import sync_playwright
import time

CDP_PORT = 9222
query = 'subject:"Retrieve AlFursan OTP"'

with sync_playwright() as p:
    try:
        browser = p.chromium.connect_over_cdp(f"http://localhost:{CDP_PORT}")
        context = browser.contexts[0] if browser.contexts else browser.new_context()
        page = context.new_page()
        page.goto("https://mail.google.com", timeout=30000)
        time.sleep(3)
        
        search_input_selector = 'input[name="q"]'
        search_box = page.locator(search_input_selector)
        
        print("Clearing and filling search box...")
        search_box.click()
        search_box.fill("") # Clear first
        time.sleep(1)
        search_box.fill(query)
        time.sleep(1)
        
        print(f"Value in search box: {search_box.input_value()}")
        
        print("Pressing Enter...")
        search_box.press("Enter")
        time.sleep(5)
        
        print(f"Current URL: {page.url}")
        print(f"Title: {page.title()}")
        
        # Take a screenshot to inspect
        screenshot_path = r"C:\Users\ashus\SaudiaAutomation\screenshots\search_debug.png"
        page.screenshot(path=screenshot_path)
        print(f"Screenshot saved to {screenshot_path}")
        
        rows = page.locator('tr.zA')
        count = rows.count()
        print(f"Found {count} email rows matching search.")
        
        page.close()
    except Exception as e:
        print(f"Error: {e}")

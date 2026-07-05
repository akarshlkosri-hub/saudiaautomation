from playwright.sync_api import sync_playwright
import time
import sys

CDP_PORT = 9222

print("Connecting to Brave via CDP...")
with sync_playwright() as p:
    try:
        browser = p.chromium.connect_over_cdp(f"http://localhost:{CDP_PORT}")
        context = browser.contexts[0] if browser.contexts else browser.new_context()
        page = context.new_page()
        
        print("Navigating to Gmail...")
        page.goto("https://mail.google.com", timeout=30000)
        time.sleep(3)
        
        # Check if search input exists
        search_input_selector = 'input[name="q"]'
        if page.locator(search_input_selector).count() > 0:
            print("Search box found.")
            search_box = page.locator(search_input_selector)
            
            # Search for Retrieve AlFursan OTP
            search_query = "Retrieve AlFursan OTP"
            print(f"Searching for '{search_query}'...")
            search_box.click()
            search_box.fill(search_query)
            search_box.press("Enter")
            
            time.sleep(4)
            
            # Print page title
            print(f"Current Title after search: {page.title()}")
            
            # List email rows if any
            rows = page.locator('tr.zA')
            count = rows.count()
            print(f"Found {count} email rows matching search.")
            
            for i in range(min(5, count)):
                row = rows.nth(i)
                text = row.inner_text().replace('\n', ' | ')
                # Safe print for Windows terminal to avoid charmap encoding errors
                safe_text = text.encode(sys.stdout.encoding, errors='replace').decode(sys.stdout.encoding)
                print(f"Row {i+1}: {safe_text}")
                
        else:
            print("Search box not found on page!")
            
        page.close()
    except Exception as e:
        print(f"Error: {e}")

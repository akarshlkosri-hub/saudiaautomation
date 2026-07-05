from playwright.sync_api import sync_playwright
import time
import sys

CDP_PORT = 9222
queries = [
    'subject:"Retrieve AlFursan OTP"',
    'subject:(Retrieve AlFursan OTP)',
    '"Retrieve AlFursan OTP"',
    'from:Saudia "Retrieve AlFursan OTP"'
]

with sync_playwright() as p:
    try:
        browser = p.chromium.connect_over_cdp(f"http://localhost:{CDP_PORT}")
        context = browser.contexts[0] if browser.contexts else browser.new_context()
        page = context.new_page()
        page.goto("https://mail.google.com", timeout=30000)
        time.sleep(3)
        
        search_input_selector = 'input[name="q"]'
        search_box = page.locator(search_input_selector)
        
        for q in queries:
            print(f"\nTesting query: {q}")
            search_box.click()
            # Clear search box first by selecting all and backspacing
            search_box.press("Control+A")
            search_box.press("Backspace")
            search_box.fill(q)
            search_box.press("Enter")
            
            time.sleep(3)
            
            rows = page.locator('tr.zA')
            count = rows.count()
            print(f"Found {count} rows.")
            
            for i in range(min(3, count)):
                row = rows.nth(i)
                text = row.inner_text().replace('\n', ' | ')
                safe_text = text.encode(sys.stdout.encoding, errors='replace').decode(sys.stdout.encoding)
                print(f"  Row {i+1}: {safe_text}")
                
        page.close()
    except Exception as e:
        print(f"Error: {e}")

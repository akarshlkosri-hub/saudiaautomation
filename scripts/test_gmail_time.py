import time
import re
from playwright.sync_api import sync_playwright

def check_gmail_time():
    with sync_playwright() as p:
        try:
            print("Starting in 3 seconds... please look at your Brave window!")
            time.sleep(3.0)
            
            print("Connecting to Brave via CDP...")
            browser = p.chromium.connect_over_cdp("http://localhost:9222")
            context = browser.contexts[0]
            page = context.new_page()
            
            print("Navigating to Gmail...")
            page.goto("https://mail.google.com/mail/u/0/#inbox", wait_until="domcontentloaded")
            
            print("Reloading page to get fresh inbox...")
            page.reload(wait_until="domcontentloaded")
            
            # STABILITY CHECK
            print("Waiting for page to become fully stable...")
            page.wait_for_selector('input[name="q"]', timeout=10000)
            page.wait_for_selector('tr.zA', timeout=10000)
            time.sleep(1.5)
            
            print("Searching for 'Retrieve AlFursan OTP'...")
            search_box = page.locator('input[name="q"]')
            search_box.click()
            search_box.fill("")
            time.sleep(0.5)
            search_box.fill('subject:"Retrieve AlFursan OTP"')
            time.sleep(0.5)
            search_box.press("Enter")
            
            print("Waiting for results...")
            time.sleep(3.0)
            
            rows = page.locator('tr.zA')
            count = rows.count()
            
            if count == 0:
                print("No emails found.")
                return
                
            print(f"Found {count} emails. Checking the first one (latest)...")
            first_row = rows.nth(0)
            
            # The time is usually in a span with class 'xW' or similar, but we can just get the inner text of the time column
            # In Gmail, the time column usually has class 'xW' inside 'xT' or 'xS' or just at the end of the row.
            # Let's extract the full row text and find the time/date at the end.
            row_text = first_row.inner_text()
            print(f"Full Row Text:\n{row_text.encode('ascii', 'ignore').decode()}")
            
            # We can isolate the last column specifically.
            time_element = first_row.locator('td.xW span')
            email_time_str = "UNKNOWN"
            if time_element.count() > 0:
                email_time_str = (time_element.first.get_attribute("title") or time_element.first.inner_text()).encode('ascii', 'ignore').decode()
            
            print(f"\n=> LATEST OTP TIME FOUND: {email_time_str}")
            
            print("Opening the matched email...")
            first_row.dispatch_event("click")
            
            # Wait for email body to load
            body_selector = '.a3s'
            page.wait_for_selector(body_selector, timeout=10000)
            email_body_element = page.locator(body_selector).first
            email_text = email_body_element.inner_text()
            
            # Extract OTP
            import re
            matches = re.findall(r'\b\d{6}\b', email_text)
            if matches:
                otp_code = matches[0]
                print(f"=> LATEST OTP CODE: {otp_code}")
            else:
                print("=> COULD NOT FIND 6-DIGIT OTP IN EMAIL BODY")
                
            print("Holding the screen for 5 seconds so you can see it...")
            time.sleep(5.0)
            page.close()
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    check_gmail_time()

import time
import re
import subprocess
import requests
from datetime import datetime, timedelta
from dateutil import parser
from playwright.sync_api import sync_playwright
import config

def is_cdp_available():
    """Check if Brave browser is already running with remote debugging enabled on port 9222"""
    try:
        resp = requests.get(f"http://localhost:{config.CDP_PORT}/json/version", timeout=2)
        if resp.status_code == 200:
            return True
    except:
        pass
    return False

def start_brave():
    """Launch Brave browser with debugging port enabled if not already running"""
    if is_cdp_available():
        print("Brave remote debugging is already running and reachable.")
        return True
        
    print("Brave debugging port not active. Launching Brave browser...")
    try:
        # Start Brave browser in a detached background process
        subprocess.Popen([
            config.BRAVE_PATH, 
            f"--remote-debugging-port={config.CDP_PORT}",
            # Use a separate user data directory if needed to avoid lock conflicts
            "--no-first-run"
        ])
        # Wait for launch
        for _ in range(6):
            time.sleep(1.0)
            if is_cdp_available():
                print("Brave browser launched successfully with remote debugging.")
                return True
    except Exception as e:
        print(f"Failed to launch Brave browser: {e}")
        
    return False

def extract_otp_from_text(text):
    """Extracts a 6-digit OTP from email body text"""
    # Look for 6-digit numbers in the text
    matches = re.findall(r'\b\d{6}\b', text)
    if matches:
        # If there are multiple, try to find one near keywords like OTP/code/verification
        for match in matches:
            # Simple context check: OTP should be the focus
            return match
    return None

def fetch_otp(request_timestamp, timeout=60):
    """
    Connects to running Brave browser via CDP, checks Gmail,
    and extracts the latest AlFursan OTP.
    Handles its own smart retry loop using page reloads.
    """
    if not is_cdp_available():
        print("ERROR: Brave remote debugging is not running! Cannot fetch OTP.")
        return None
        
    print("Connecting to Brave via CDP...")
    with sync_playwright() as p:
        try:
            browser = p.chromium.connect_over_cdp(f"http://localhost:{config.CDP_PORT}")
            context = browser.contexts[0] if browser.contexts else browser.new_context()
            page = context.new_page()
            
            print("Navigating to Gmail...")
            page.goto("https://mail.google.com/mail/u/0/#inbox", wait_until="domcontentloaded", timeout=30000)
            time.sleep(2.0)

            if "signin" in page.url or "accounts.google.com" in page.url:
                print("\n" + "="*60)
                print("WARNING: Gmail is NOT logged in Brave!")
                print("Please log in to Gmail manually in the Brave browser window.")
                print("="*60 + "\n")
                page.close()
                return None
                
            search_input_selector = 'input[name="q"]'
            start_time = time.time()
            attempt = 1
            
            # Smart retry loop using a single tab
            while time.time() - start_time < timeout:
                print(f"\n--- OTP Fetch Attempt {attempt} ---")
                
                try:
                    page.wait_for_selector(search_input_selector, timeout=10000)
                except Exception:
                    print("Gmail inbox interface did not load in time. Reloading...")
                    page.reload(wait_until="domcontentloaded", timeout=30000)
                    time.sleep(2.0)
                    continue

                print(f"Searching for subject: '{config.OTP_EMAIL_SUBJECT}' (newer_than:1h)...")
                search_box = page.locator(search_input_selector)
                search_box.click()
                search_box.fill("")  # Clear search box
                time.sleep(0.5)
                # Use newer_than:1h to filter out very old noise
                search_box.fill(f'is:unread subject:"{config.OTP_EMAIL_SUBJECT}" newer_than:1h')
                search_box.press("Enter")
                
                # Wait for search URL to activate
                for _ in range(10):
                    if "#search/" in page.url:
                        break
                    time.sleep(0.5)
                    
                time.sleep(2.0) # Let the results render
                
                rows = page.locator('tr.zA')
                if rows.count() == 0:
                    print("No unread OTP emails found in the last hour.")
                else:
                    target_row = None
                    # Find the first email row that actually matches the subject text
                    for i in range(rows.count()):
                        row = rows.nth(i)
                        if "Retrieve AlFursan OTP" in row.inner_text():
                            target_row = row
                            break
                            
                    if target_row:
                        print("Found matching email. Opening...")
                        target_row.dispatch_event("click")
                        
                        # Wait for email body to load
                        body_selector = '.a3s'
                        try:
                            page.wait_for_selector(body_selector, timeout=10000)
                        except:
                            print("Email body did not load.")
                            page.goto("https://mail.google.com/mail/u/0/#inbox", wait_until="domcontentloaded")
                            continue
                            
                        # Extract Timestamp
                        # The time is usually in the element with class 'g3' inside the email header
                        # The title attribute often contains the full date string (e.g. 'Jul 3, 2026, 5:29 PM')
                        time_elements = page.locator('.g3')
                        email_time_str = None
                        if time_elements.count() > 0:
                            email_time_str = time_elements.last.get_attribute('title')
                            
                        if not email_time_str and time_elements.count() > 0:
                            # Fallback to inner text
                            email_time_str = time_elements.last.inner_text()

                        safe_time_str = email_time_str.encode('ascii', 'ignore').decode('ascii') if email_time_str else "None"
                        print(f"Extracted email timestamp string: {safe_time_str}")
                        
                        is_fresh = False
                        if email_time_str:
                            try:
                                # Clean up string and parse using safe ascii string
                                clean_time_str = re.sub(r'\(.*?\)', '', safe_time_str).strip()
                                email_dt = parser.parse(clean_time_str).replace(tzinfo=None)
                                request_dt = request_timestamp.replace(tzinfo=None)
                                
                                print(f"Parsed email time: {email_dt} | Request time: {request_dt}")
                                
                                # 1 minute buffer for clock drift
                                if email_dt >= request_dt - timedelta(minutes=1):
                                    is_fresh = True
                                    print("[FRESH] Email timestamp is valid!")
                                else:
                                    print("[STALE] Email arrived before OTP was triggered.")
                            except Exception as e:
                                print(f"Error parsing timestamp: {e}. Assuming fresh as fallback.")
                                is_fresh = True
                        else:
                            print("Could not find timestamp. Assuming fresh as fallback.")
                            is_fresh = True
                            
                        if is_fresh:
                            # Extract email content
                            email_body_element = page.locator(body_selector).last
                            email_text = email_body_element.inner_text()
                            
                            # Extract OTP
                            otp = extract_otp_from_text(email_text)
                            if otp:
                                print(f"Extracted OTP candidate: {otp}")
                                
                                # Try deleting
                                try:
                                    delete_btn = page.locator('div[aria-label="Delete"], div[data-tooltip="Delete"]').nth(1)
                                    if delete_btn.count() > 0:
                                        delete_btn.click()
                                        time.sleep(1.0)
                                except:
                                    pass
                                
                                print(f"SUCCESS: OTP {otp} retrieved!")
                                page.close()
                                return otp
                            else:
                                print("Failed to find 6-digit OTP in the fresh email body.")
                        
                        # Go back to inbox for next loop
                        page.goto("https://mail.google.com/mail/u/0/#inbox", wait_until="domcontentloaded")
                
                # Wait before next attempt
                attempt += 1
                wait_time = 15
                elapsed = int(time.time() - start_time)
                if elapsed + wait_time < timeout:
                    print(f"Waiting {wait_time} seconds before reloading inbox... ({elapsed}s/{timeout}s elapsed)")
                    time.sleep(wait_time)
                    print("Reloading page...")
                    page.reload(wait_until="domcontentloaded", timeout=30000)
                    time.sleep(2.0)
                else:
                    break
                    
            print("ERROR: Timeout reached waiting for FRESH OTP email.")
            page.close()
            
        except Exception as e:
            print(f"Error during Gmail OTP extraction: {e}")
            
    return None

def wait_for_otp(request_timestamp, timeout=60, interval=5):
    """Backward compatibility wrapper. Interval is ignored as fetch_otp handles its own 15s loop."""
    return fetch_otp(request_timestamp, timeout=timeout)

if __name__ == "__main__":
    print("=== TESTING GMAIL OTP MODULE ===")
    
    # 1. Launch Brave
    success = start_brave()
    if not success:
        print("ERROR: Could not launch or connect to Brave debugging session.")
        exit(1)
        
    print("\nBrave is ready. Please ensure your Gmail client is open and logged in.")
    input("Press ENTER to attempt to read latest OTP email...")
    
    timestamp = datetime.now()
    otp = fetch_otp(timestamp)
    
    if otp:
        print(f"\nSUCCESS: Test OTP read: {otp}")
    else:
        print("\nFAILED: Could not read OTP from Gmail. Check logs above.")

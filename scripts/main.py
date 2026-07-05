import time
import os
import sys
import subprocess
from datetime import datetime

# Add scripts directory to path to ensure clean imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import config
import excel_reader
import phone_control
import gmail_otp

def setup_logging():
    """Create timestamped log file in logs directory"""
    os.makedirs(config.LOG_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(config.LOG_DIR, f"run_{timestamp}.log")
    
    # Custom print function that writes to both terminal and log file
    class Logger:
        def __init__(self, filepath):
            self.terminal = sys.stdout
            self.log = open(filepath, "w", encoding="utf-8")
            
        def write(self, message):
            self.terminal.write(message)
            self.log.write(message)
            self.log.flush()
            
        def flush(self):
            self.terminal.flush()
            self.log.flush()
            
    sys.stdout = Logger(log_file)
    print(f"Logging initialized. Output saved to: {log_file}")

def verify_login_success():
    """
    Checks the current phone screen elements to determine if login was successful.
    After OTP + swipe up + app restart, the dashboard should show member info.
    """
    print("Verifying login status on device screen...")
    elements, activity = phone_control.get_screen_elements()
    
    for el in elements:
        text = el.get('text', '').lower()
        desc = el.get('content_desc', '').lower()
        search_str = text + " " + desc
        # Look for actual dashboard keywords from real screen dump
        if any(kw in search_str for kw in ["hi, ", "green member", "reward miles", "your trips", "book a flight", "log out", "sign out"]):
            print(f"Login success indicator found: '{search_str}'")
            return True, search_str
        # Also check content_desc for "Home" (the dashboard page identifier)
        if desc == "home":
            print(f"Login success indicator found: content_desc='Home'")
            return True, "Dashboard Home page"
            
    return False, "Dashboard indicators not found. Still on OTP or unknown state."

def run_automation():
    print("="*60)
    print("         SAUDIA AIRLINES LOGIN AUTOMATION")
    print("="*60)
    
    # 1. Check phone connection
    print("Performing device connectivity health check...")
    if not phone_control.check_health():
        print("CRITICAL ERROR: Accessibility Server not reachable on phone!")
        print("Please check your WiFi, IP address, and toggle Accessibility Service ON.")
        return
    print("Device connectivity: OK")
    
    # 2. Check and start Brave
    print("Checking Brave browser debugging port...")
    if not gmail_otp.start_brave():
        print("CRITICAL ERROR: Brave browser remote debugging could not be initialized.")
        print("Please close all Brave windows manually and run this script again.")
        return
    print("Brave browser status: OK")
    
    # 3. Read passengers from Excel
    print("Reading passenger list from Excel...")
    try:
        passengers = excel_reader.get_pending_passengers()
    except Exception as e:
        print(f"CRITICAL ERROR: Failed to read passengers.xlsx: {e}")
        return
        
    if not passengers:
        print("No pending passengers found in passengers.xlsx. All rows marked 'Success' or 'Failed'.")
        return
        
    print(f"Successfully loaded {len(passengers)} pending passenger records.")
    
    current_gmail = None
    success_count = 0
    fail_count = 0
    
    # 4. Process loop
    for i, p in enumerate(passengers):
        row_num = p['row']
        gmail_id = p['gmail']
        ffn = p['ffn']
        password = p['password']
        
        print("\n" + "="*50)
        print(f"Processing Record {i+1}/{len(passengers)} [Row {row_num}]")
        print(f"FFN: {ffn} | Gmail: {gmail_id}")
        print("="*50)
        
        # 5. Handle Gmail Account Switch
        if gmail_id != current_gmail:
            print(f"\n[ACTION REQUIRED] Please switch Gmail account in Brave.")
            print(f"--> Target Gmail: {gmail_id}")
            print("Make sure Gmail is open and active in Brave browser.")
            print("Waiting for ready.txt flag to proceed...")
            ready_file = os.path.join(os.path.dirname(__file__), "..", "ready.txt")
            if os.path.exists(ready_file):
                os.remove(ready_file)
            while not os.path.exists(ready_file):
                time.sleep(1.0)
            os.remove(ready_file)
            current_gmail = gmail_id
            
        try:
            # 6. Execute app login flow on phone
            print("Initiating login sequence on phone...")
            otp_request_time = phone_control.login_to_saudia(ffn, password)
            
            # 7. Fetch OTP from Gmail
            print("Polling Gmail for verification code...")
            # We pass request timestamp to verify email is new
            otp_code = gmail_otp.wait_for_otp(otp_request_time, timeout=120, interval=5)
            
            if not otp_code:
                raise Exception("OTP Fetch Timeout: No new OTP email found within 120 seconds.")
                
            # 8. Enter OTP in app (No retry loop needed as gmail_otp guarantees fresh OTP)
            login_success = False
            print(f"Entering OTP code {otp_code} into the Saudia app...")
            phone_control.enter_otp(otp_code)
            
            # Wait for app to process OTP
            print("Waiting 5 seconds for OTP processing...")
            time.sleep(5.0)
            
            # Check if we moved past OTP screen (Verify mobile number or dashboard)
            elements, _ = phone_control.get_screen_elements()
            screen_texts = " ".join([el.get('text', '') for el in elements]).lower()
            
            if "verify mobile number" in screen_texts:
                # OTP was accepted! Now bypass this screen by restarting the app (Gotcha #6)
                print("'Verify mobile number' screen detected. OTP accepted!")
                print("Bypassing verification screen via app restart...")
                phone_control.restart_app()
                time.sleep(3.0) # Additional buffer for the dashboard to settle
                
                # Now verify we're on the dashboard
                logged_in, msg = verify_login_success()
                if logged_in:
                    print(f"SUCCESS: FFN {ffn} logged in successfully! ({msg})")
                    excel_reader.update_status(row_num, "Success", f"Logged in with OTP: {otp_code}")
                    success_count += 1
                    login_success = True
                    print("\n[PAUSE AS REQUESTED] Reached logged-in condition. Stopping script here.")
                    sys.exit(0)
                else:
                    print(f"OTP entered and bypass attempted, but dashboard not found. {msg}")
            
            elif "verification" in screen_texts or "otp" in screen_texts:
                # Still on OTP screen - OTP was wrong or expired
                print(f"OTP {otp_code} failed: Still on OTP/verification screen.")
            else:
                # Unknown screen - try verify anyway
                logged_in, msg = verify_login_success()
                if logged_in:
                    print(f"SUCCESS: FFN {ffn} logged in successfully! ({msg})")
                    excel_reader.update_status(row_num, "Success", f"Logged in with OTP: {otp_code}")
                    success_count += 1
                    login_success = True
                    print("\n[PAUSE AS REQUESTED] Reached logged-in condition. Stopping script here.")
                    sys.exit(0)
                else:
                    print(f"OTP entered but unknown screen state reached. {msg}")
        
            if not login_success:
                raise Exception(f"Login failed after OTP entry. Last known state: {screen_texts[:50]}")
                
        except Exception as e:
            err_msg = str(e)
            print(f"ERROR processing Row {row_num}: {err_msg}")
            excel_reader.update_status(row_num, "Failed", err_msg)
            fail_count += 1
            
        # 10. Capture screenshot for records
        screenshot_name = f"row_{row_num}_final"
        phone_control.take_screenshot(screenshot_name)
        
    print("\n" + "="*60)
    print("                    RUN COMPLETED")
    print(f"Total processed: {len(passengers)}")
    print(f"Success: {success_count} | Failed: {fail_count}")
    print("="*60)

if __name__ == "__main__":
    setup_logging()
    run_automation()

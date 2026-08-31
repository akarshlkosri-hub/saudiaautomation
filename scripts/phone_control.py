import requests
import subprocess
import time
import os
import config
from datetime import datetime

def check_health():
    """Verify phone connection to Accessibility HTTP Server"""
    try:
        resp = requests.get(f"{config.PHONE_BASE_URL}/health", timeout=5)
        if resp.status_code == 200 and resp.json().get('status') == 'connected':
            return True
    except Exception as e:
        print(f"Health check warning: {e}")
    return False

def get_screen_elements():
    """Fetch all screen elements from phone and format them similarly to remote_control.py"""
    try:
        resp = requests.get(f"{config.PHONE_BASE_URL}/screen", timeout=10)
        data = resp.json()
        elements = data.get('elements', [])
        
        # Build list of interactive/important elements
        interactive = []
        for el in elements:
            text = el.get('text', '') or ''
            res_id = el.get('resource_id', '') or ''
            content_desc = el.get('content_desc', '') or ''
            cls = el.get('class', '') or ''
            clickable = el.get('clickable', False)
            bounds = el.get('bounds', '')
            
            is_edit_text = "EditText" in cls
            if text or res_id or content_desc or clickable or is_edit_text:
                interactive.append({
                    'text': text,
                    'resource_id': res_id,
                    'content_desc': content_desc,
                    'class': cls,
                    'clickable': clickable,
                    'bounds': bounds
                })
        return interactive, data.get('activity', 'Unknown')
    except Exception as e:
        print(f"Error fetching screen: {e}")
        return [], "Error"

def parse_bounds(bounds_str):
    """Parse bounds string like '841 2024 1049 2182' and return center (x, y)"""
    try:
        parts = bounds_str.strip().split()
        if len(parts) == 4:
            left, top, right, bottom = map(int, parts)
            cx = left + (right - left) // 2
            cy = top + (bottom - top) // 2
            return cx, cy
    except Exception as e:
        print(f"Error parsing bounds '{bounds_str}': {e}")
    return None

def adb_tap(x, y):
    """Tap at coordinates on the device using ADB"""
    subprocess.run([config.ADB_PATH, "shell", "input", "tap", str(x), str(y)], capture_output=True)
    return {"success": True, "method": "adb_tap"}

def adb_type_text(text):
    """Type text char-by-char using ADB with 250ms delay for stability"""
    for char in text:
        # ADB text spaces need to be escaped as %s
        adb_char = char.replace(" ", "%s")
        subprocess.run([config.ADB_PATH, "shell", "input", "text", adb_char], capture_output=True)
        time.sleep(0.25)
    return {"success": True, "method": "adb_type"}

def click_element(el):
    """Clicks an element. Tries HTTP first, falls back to ADB tap using bounds."""
    result = {"success": False}
    
    # 1. Try Accessibility Click by Text
    if el.get('text'):
        try:
            resp = requests.post(f"{config.PHONE_BASE_URL}/action/click", json={"text": el['text']}, timeout=5)
            result = resp.json()
        except Exception as e:
            print(f"HTTP text click error: {e}")
            
    # 2. Try Accessibility Click by ID
    if not result.get('success') and el.get('resource_id'):
        try:
            resp = requests.post(f"{config.PHONE_BASE_URL}/action/click", json={"resource_id": el['resource_id']}, timeout=5)
            result = resp.json()
        except Exception as e:
            print(f"HTTP ID click error: {e}")
            
    # 3. Fallback: ADB Tap center of element bounds
    if not result.get('success') and el.get('bounds'):
        coords = parse_bounds(el['bounds'])
        if coords:
            print(f"Click fallback: ADB Tapping at center ({coords[0]}, {coords[1]})")
            result = adb_tap(coords[0], coords[1])
            
    return result

def type_in_field(el, text):
    """Types text into an element. Tries HTTP API first, falls back to ADB tap-and-type."""
    result = {"success": False}
    
    # 1. Try HTTP API Type
    if el.get('resource_id'):
        try:
            resp = requests.post(f"{config.PHONE_BASE_URL}/action/type", json={"resource_id": el['resource_id'], "text": text}, timeout=10)
            result = resp.json()
        except Exception as e:
            print(f"HTTP type error: {e}")
            
    # 2. Fallback: ADB tap and char-by-char type
    if not result.get('success') and el.get('bounds'):
        coords = parse_bounds(el['bounds'])
        if coords:
            print(f"Type fallback: Tapping element to focus and typing via ADB...")
            adb_tap(coords[0], coords[1])
            time.sleep(0.5)
            # Clear field first by sending 25 backspace keyevents
            print("Clearing existing text in field...")
            backspaces = ["67"] * 25
            subprocess.run([config.ADB_PATH, "shell", "input", "keyevent"] + backspaces, capture_output=True)
            time.sleep(0.3)
            result = adb_type_text(text)
            
    return result

def enter_otp(otp_code, otp_field=None):
    """
    Inputs OTP digits. We must use ADB typing because ACTION_SET_TEXT 
    bypasses the app's IME listeners, preventing it from auto-submitting.
    """
    print(f"Entering OTP: {otp_code}")
    
    # Locate OTP field to focus it
    if not otp_field:
        print("Waiting for OTP field to appear...")
        for _ in range(8):
            elements, _ = get_screen_elements()
            for el in elements:
                desc = (el.get('content_desc', '') or '').lower()
                if "verification code" in desc or "verification" in desc or "otp" in desc:
                    otp_field = el
                    print(f"DEBUG: Matched OTP field: {el}")
                    break
            if otp_field:
                break
            time.sleep(1.0)
            
    if otp_field and otp_field.get('bounds'):
        parts = otp_field['bounds'].strip().split()
        left, top, right, bottom = map(int, parts)
        tap_x = left + 40  # Tap 40 pixels from the left to focus the first digit box
        tap_y = (top + bottom) // 2
        print(f"Tapping OTP field at far-left ({tap_x}, {tap_y}) to ensure focus...")
        adb_tap(tap_x, tap_y)
        time.sleep(1.0)
            
    print("Using ADB typing to trigger auto-submit listeners...")
    return adb_type_text(otp_code)

def resend_otp():
    """
    Taps the 'Resend code' button area on the OTP screen.
    Based on otpscreen.xml dump, it's a view at [405,919][675,1054].
    """
    print("Tapping 'Resend code' area...")
    # Center of [405,919][675,1054] is x=540, y=986
    adb_tap(540, 986)
    return datetime.now()

def press_back():
    """Send back command. Try HTTP first, fall back to ADB keyevent 4"""
    try:
        resp = requests.post(f"{config.PHONE_BASE_URL}/action/back", timeout=5)
        if resp.status_code == 200:
            return resp.json()
    except Exception as e:
        print(f"HTTP back error: {e}")
    # ADB fallback
    subprocess.run([config.ADB_PATH, "shell", "input", "keyevent", "4"], capture_output=True)
    return {"success": True, "method": "adb"}

def restart_app():
    """Kill app, wait 3s, launch fresh and wait 4s"""
    print("Force stopping Saudia app...")
    subprocess.run([config.ADB_PATH, "shell", "am force-stop", "com.saudia.SaudiaApp"], capture_output=True)
    time.sleep(config.APP_RESTART_DELAY)
    print("Launching Saudia app fresh...")
    subprocess.run([config.ADB_PATH, "shell", "monkey -p com.saudia.SaudiaApp -c android.intent.category.LAUNCHER 1"], capture_output=True)
    # Wait for splash screen / loading
    time.sleep(4.0)
    print("App launch command sent.")

def take_screenshot(name):
    """Take device screenshot and pull to screenshots folder"""
    os.makedirs(config.SCREENSHOT_DIR, exist_ok=True)
    filename = f"{name}.png"
    filepath = os.path.join(config.SCREENSHOT_DIR, filename)
    try:
        subprocess.run([config.ADB_PATH, "shell", "screencap", "-p", "/sdcard/screen.png"], capture_output=True)
        subprocess.run([config.ADB_PATH, "pull", "/sdcard/screen.png", filepath], capture_output=True)
        print(f"Screenshot saved to: {filepath}")
        return filepath
    except Exception as e:
        print(f"Error capturing screenshot: {e}")
    return None

def login_to_saudia(ffn, password):
    """
    Main login sequence for Saudia App.
    Uses resilient polling loops to wait for UI transitions.
    """
    # 1. Restart App
    restart_app()
    
    # 2. Find AlFursan Tab (Poll for up to 12 seconds)
    alfursan_tab = None
    print("Waiting for AlFursan tab to appear...")
    for _ in range(12):
        elements, activity = get_screen_elements()
        for el in elements:
            text = el.get('text', '') or ''
            desc = el.get('content_desc', '') or ''
            if ("alfursan" in text.lower() or "alfursan" in desc.lower()) and ("tab" in text.lower() or "tab" in desc.lower()):
                alfursan_tab = el
                break
        if alfursan_tab:
            break
        time.sleep(1.0)
            
    if not alfursan_tab:
        raise Exception("Timeout: Could not find 'AlFursan' tab on Home screen!")
        
    print(f"Clicking AlFursan Tab: {alfursan_tab.get('text') or alfursan_tab.get('content_desc')}")
    click_element(alfursan_tab)
    
    # 3. Click Login Button (Poll for up to 8 seconds)
    login_btn_top = None
    print("Waiting for Login button at top right...")
    for _ in range(8):
        elements, activity = get_screen_elements()
        for el in elements:
            text = el.get('text', '').strip()
            if text.lower() == "login":
                login_btn_top = el
                break
        if login_btn_top:
            break
        time.sleep(1.0)
            
    if not login_btn_top:
        raise Exception("Timeout: Could not find 'Login' button on AlFursan screen!")
        
    print("Clicking Login button at top right...")
    click_element(login_btn_top)
    
    # 4. Fill form (FFN & Password) - Poll for form fields up to 8 seconds
    edit_texts = []
    print("Waiting for Login form input fields...")
    for _ in range(8):
        elements, activity = get_screen_elements()
        edit_texts = [el for el in elements if "EditText" in el.get('class', '')]
        if len(edit_texts) >= 2:
            break
        time.sleep(1.0)
    
    if len(edit_texts) < 2:
        raise Exception(f"Timeout: Expected at least 2 input fields (FFN + Pass) on Login form, found {len(edit_texts)}")
        
    ffn_field = edit_texts[0]
    pass_field = edit_texts[1]
    
    print(f"Typing FFN: {ffn}")
    type_in_field(ffn_field, ffn)
    time.sleep(0.5)
    
    print("Typing Password...")
    type_in_field(pass_field, password)
    time.sleep(1.0)
    
    # Hide soft keyboard safely using ESCAPE (keyevent 111) which does not dismiss the bottom sheet
    print("Hiding soft keyboard by sending ESCAPE (111) keyevent...")
    subprocess.run([config.ADB_PATH, "shell", "input", "keyevent", "111"], capture_output=True)
    time.sleep(1.5)
    
    # 5. Locate & Click Login Submit Button (Poll for up to 8 seconds)
    # IMPORTANT: The Saudia app has content_desc="Login Button" on the submit button.
    login_submit_btn = None
    print("Locating Login Submit Button on form...")
    for _ in range(8):
        elements, activity = get_screen_elements()
        
        # Pass 1: Exact match on content_desc == "Login Button"
        for el in elements:
            desc = (el.get('content_desc', '') or '').strip()
            if desc.lower() == "login button":
                login_submit_btn = el
                print(f"Found Login Button by exact content_desc match: '{desc}'")
                break
        if login_submit_btn:
            break
            
        # Pass 2: Fuzzy match but EXCLUDE Gmail/Apple/graphic link elements
        for el in elements:
            text = el.get('text', '') or ''
            desc = el.get('content_desc', '') or ''
            search_str = (text + " " + desc).lower()
            
            # Skip Gmail, Apple, and graphic link buttons
            if any(skip in search_str for skip in ["gmail", "apple", "graphic"]):
                continue
                
            if "login" in search_str and "button" in search_str:
                bounds = parse_bounds(el.get('bounds', ''))
                if bounds and bounds[1] > 300:
                    login_submit_btn = el
                    print(f"Found Login Button by fuzzy match: text='{text}' desc='{desc}'")
                    break
        if login_submit_btn:
            break
        time.sleep(1.0)
                
    if not login_submit_btn:
        raise Exception("Timeout: Could not locate Login Submit Button on form!")
        
    print("Clicking Login Submit Button...")
    click_element(login_submit_btn)
    time.sleep(1.5)
    
    # Return timestamp of OTP request
    otp_time = datetime.now()
    print(f"Login form submitted at: {otp_time.isoformat()}")
    return otp_time

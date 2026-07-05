# Saudia App Login Automation — BLUEPRINT

> **This file is the master reference for any AI model working on this project.**
> Read this COMPLETELY before writing any code.

---

## Project Overview

Automate Saudia Airlines AlFursan login for 100-150 passengers daily:
1. Read FFN + Password from Excel
2. Login to Saudia app on Android phone (via HTTP API on port 5000)
3. Fetch OTP from already-logged-in Gmail in Brave browser
4. Enter OTP in app → Login complete
5. Repeat for each Excel row

**Scope:** Only LOGIN flow. Post-login actions are future phase.

---

## Architecture

```
┌──────────────┐     HTTP API      ┌─────────────────────┐
│  PC (Python)  │ ◄──────────────► │  Android Phone      │
│               │   port 5000      │  (SaudiaWorker APK) │
│  main.py      │                  │                     │
│  ├─ excel     │     ADB USB      │  Saudia Airlines    │
│  ├─ phone_ctl │ ◄──────────────► │  App                │
│  └─ gmail_otp │                  └─────────────────────┘
│       │       │
│       ▼       │     CDP 9222     ┌─────────────────────┐
│  Playwright   │ ◄──────────────► │  Brave Browser      │
│               │                  │  (Gmail logged in)  │
└──────────────┘                  └─────────────────────┘
```

---

## Semi-Automated Flow

**USER handles:** Gmail login in Brave (including 2FA)
**SCRIPT handles:** Everything else (app login, OTP fetch, OTP entry)

```
For each passenger:
  1. Script shows Gmail ID needed (from Excel Col D)
  2. If Gmail changed → Script pauses, user switches Gmail in Brave, presses ENTER
  3. Script restarts Saudia app (force-stop + 3s delay + fresh launch)
  4. Script clicks AlFursan tab → Login button
  5. Script types FFN (Col E) + Password (Col F) → clicks Login
  6. Script notes timestamp → polls Gmail for OTP email
  7. Script extracts 6-digit OTP from email with subject "Retrieve AlFursan OTP"
  8. Script enters OTP in app (char-by-char, 250ms delay)
  9. Script verifies login → updates Excel Status (Col K) + Remarks (Col L)
  10. Next passenger
```

---

## Folder Structure

```
C:\Users\ashus\SaudiaAutomation\
├── BLUEPRINT.md                   ← THIS FILE (master reference)
├── data/
│   └── passengers.xlsx            ← User's Excel file
├── scripts/
│   ├── config.py                  ← All settings
│   ├── excel_reader.py            ← Read/write Excel
│   ├── phone_control.py           ← Phone HTTP API + ADB
│   ├── gmail_otp.py               ← OTP fetch from Brave/Gmail
│   └── main.py                    ← Main orchestrator
├── logs/                          ← Run logs
├── screenshots/                   ← Phone screenshots
└── requirements.txt               ← Dependencies
```

---

## Excel Format (passengers.xlsx)

| Col | Header | Used Now? | Purpose |
|-----|--------|-----------|---------|
| A | PNR | No | Future |
| B | Last Name | No | Future |
| C | Full Name | No | Future |
| D | Gmail ID | **YES** | Script shows which Gmail to login |
| **E** | **FFN** | **YES** | Entered in Saudia app |
| **F** | **Password** | **YES** | Entered in Saudia app |
| G | Ticket Number | No | Future |
| H | Class | No | Future |
| I | Sec 1 | No | Future |
| J | Sec 2 | No | Future |
| **K** | **Status** | **AUTO** | Script writes: Success/Failed/OTP Timeout |
| **L** | **Remarks** | **AUTO** | Script writes: error details |

Row 1 = Headers. Data starts from Row 2.

---

## File-by-File Specifications

### 1. config.py

All constants in one place:

```python
# Phone
DEVICE_IP = "192.168.1.3"
PHONE_PORT = 5000
PHONE_BASE_URL = f"http://{DEVICE_IP}:{PHONE_PORT}"
ADB_PATH = r"C:\Users\ashus\AppData\Local\Android\Sdk\platform-tools\adb.exe"

# Excel
EXCEL_PATH = r"C:\Users\ashus\SaudiaAutomation\data\passengers.xlsx"
COL_GMAIL = 4       # D (1-indexed for openpyxl)
COL_FFN = 5         # E
COL_PASSWORD = 6    # F
COL_STATUS = 11     # K
COL_REMARKS = 12    # L

# Brave browser
BRAVE_PATH = r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"
CDP_PORT = 9222

# Timing
OTP_WAIT_TIMEOUT = 120
OTP_POLL_INTERVAL = 5
APP_RESTART_DELAY = 3

# OTP
OTP_EMAIL_SUBJECT = "Retrieve AlFursan OTP"
OTP_LENGTH = 6
```

---

### 2. excel_reader.py

Uses `openpyxl`. Functions:

| Function | Input | Output |
|----------|-------|--------|
| `get_pending_passengers()` | — | List of dicts: `{row, ffn, password, gmail}` where Status is empty |
| `update_status(row, status, remarks)` | row number, "Success"/"Failed", error text | Writes to Col K, L and saves |
| `get_gmail_for_row(row)` | row number | Gmail string from Col D |

**Important:** Sort results by Gmail ID so same-Gmail passengers are grouped together.

---

### 3. phone_control.py

Reuse logic from existing `C:\Users\ashus\PNR\remote_control.py`. Same HTTP endpoints + ADB fallbacks.

| Function | Purpose |
|----------|---------|
| `check_health()` | GET `/health` → returns True/False |
| `get_screen_elements()` | GET `/screen` → returns list of elements |
| `find_element(text)` | Search elements for text match, return index + element |
| `click_element(index, elements)` | POST `/action/click` + ADB tap fallback |
| `click_by_text(text)` | find_element + click_element combined |
| `type_in_field(index, text, elements)` | POST `/action/type` + ADB char-by-char fallback (250ms/char) |
| `enter_otp(code)` | ADB char-by-char typing with 250ms delay |
| `press_back()` | POST `/action/back` + ADB keyevent 4 fallback |
| `restart_app()` | ADB force-stop → sleep(3) → monkey launch → sleep(4) |
| `take_screenshot(name)` | ADB screencap + pull |

**High-level function:**
```python
def login_to_saudia(ffn, password):
    """
    1. restart_app()
    2. Get screen elements
    3. Find and click "AlFursan" tab
    4. Find and click "Login" button  
    5. Get screen elements (login form)
    6. Find FFN EditText → type ffn
    7. Find Password EditText → type password
    8. Find and click Login/Submit button
    9. Return datetime.now() as otp_request_timestamp
    """
```

**ADB fallback for typing:**
```python
def adb_type_text(text):
    for char in text:
        subprocess.run([ADB, "shell", "input", "text", char])
        time.sleep(0.25)  # 250ms delay between chars
```

**Parse bounds for ADB tap:**
```python
def parse_bounds(bounds_str):
    # "841 2024 1049 2182" → center (945, 2103)
    parts = bounds_str.strip().split()
    left, top, right, bottom = map(int, parts)
    return (left + right) // 2, (top + bottom) // 2
```

---

### 4. gmail_otp.py

Uses Playwright CDP to connect to user's already-running Brave browser.

**Startup:**
```python
def start_brave():
    """Launch Brave with --remote-debugging-port=9222 if not already running"""
    subprocess.Popen([BRAVE_PATH, "--remote-debugging-port=" + str(CDP_PORT)])
    time.sleep(3)  # Wait for browser to start

def connect_to_brave():
    """Connect Playwright to running Brave via CDP"""
    from playwright.sync_api import sync_playwright
    pw = sync_playwright().start()
    browser = pw.chromium.connect_over_cdp(f"http://localhost:{CDP_PORT}")
    return browser, pw
```

**OTP Fetch (Smart Retry Loop):**
```python
def fetch_otp(request_timestamp, timeout=60):
    """
    1. Connect to Brave via CDP and open a single new tab (inbox).
    2. Enter loop (until timeout):
       a. Search: is:unread subject:"Retrieve AlFursan OTP" newer_than:1h
       b. Wait for rows, click first matching email.
       c. Extract email timestamp (from .g3 title attribute).
       d. Parse timestamp safely with dateutil.parser (stripping unicode like \\u202f).
       e. Compare with request_timestamp:
          - If email_dt >= request_dt - 1m buffer: Extract OTP and return.
          - If STALE: Log warning, go back to inbox.
       f. Wait 15s, reload page, repeat loop.
    3. Return None if timeout reached.
    """
```

**Key Improvements for Stability:**
- **Tab Reuse & Reload:** Instead of opening/closing tabs repeatedly, it reuses a single tab and calls `page.reload()` every 15s. This is significantly faster and more reliable.
- **Timestamp Validation:** It actually parses the exact email receipt time from the Gmail DOM and strictly compares it against `otp_request_time`. This guarantees it will NEVER use a stale OTP, even if an old email wasn't deleted.
- **Windows Print Safety:** Strips unicode characters from the timestamp string before printing to prevent `cp1252` encoding crashes on Windows cmd.
```python
def wait_for_otp(request_timestamp, timeout=120, interval=5):
    start = time.time()
    while time.time() - start < timeout:
        otp = fetch_otp(request_timestamp)
        if otp:
            return otp
        print(f"OTP not found yet, waiting {interval}s...")
        time.sleep(interval)
    return None  # Timeout
```

---

### 5. main.py

The orchestrator:

```python
def main():
    # 1. Startup checks
    if not phone_control.check_health():
        print("ERROR: Phone not connected!")
        return
    
    start_brave()  # Launch Brave with CDP port
    
    # 2. Load passengers
    passengers = excel_reader.get_pending_passengers()  # sorted by gmail
    print(f"Pending: {len(passengers)} passengers")
    
    current_gmail = None
    success_count = 0
    fail_count = 0
    
    # 3. Main loop
    for i, p in enumerate(passengers):
        print(f"\n{'='*50}")
        print(f"Passenger {i+1}/{len(passengers)}: FFN={p['ffn']}, Gmail={p['gmail']}")
        
        # 4. Gmail switch check
        if p['gmail'] != current_gmail:
            print(f"\nSwitch Gmail to: {p['gmail']}")
            input("Press ENTER when Gmail is logged in Brave...")
            current_gmail = p['gmail']
        
        try:
            # 5. Login on phone
            otp_request_time = phone_control.login_to_saudia(p['ffn'], p['password'])
            
            # 6. Fetch OTP from Gmail
            otp = gmail_otp.wait_for_otp(otp_request_time)
            if not otp:
                raise Exception("OTP Timeout - email not found in 120 seconds")
            
            # 7. Enter OTP in app
            phone_control.enter_otp(otp)
            time.sleep(3)
            
            # 8. Verify & update
            excel_reader.update_status(p['row'], "Success", f"OTP: {otp}")
            success_count += 1
            
        except Exception as e:
            excel_reader.update_status(p['row'], "Failed", str(e))
            fail_count += 1
        
        # 9. Screenshot
        phone_control.take_screenshot(f"passenger_{p['row']}")
    
    # 10. Summary
    print(f"\nDONE: {success_count} success, {fail_count} failed")
```

---

## Phone HTTP API Reference (Already Built)

| Endpoint | Method | Body | Response |
|----------|--------|------|----------|
| `/health` | GET | — | `{"status": "connected"}` |
| `/screen` | GET | — | `{"activity": "...", "elements": [...]}` |
| `/action/click` | POST | `{"text": "..."}` or `{"resource_id": "..."}` | `{"success": true/false}` |
| `/action/type` | POST | `{"resource_id": "...", "text": "..."}` | `{"success": true/false}` |
| `/action/otp` | POST | `{"otp": "123456"}` | `{"success": true/false}` |
| `/action/back` | POST | — | `{"success": true/false}` |

---

## Known Gotchas (From Phase 1 Testing)

1. **Element numbers shift** after typing — always refresh screen before clicking
2. **OTP must be typed char-by-char** with 250ms delay (ADB method). `ACTION_SET_TEXT` bypasses auto-submit listeners.
3. **Bounds format** = space-separated: `"left top right bottom"`
4. **Phone IP changes** on WiFi reconnect — update config.py
5. **After app restart**, wait 4 seconds before screen dump
6. **"Verify mobile number" screen** after login → handle with restart_app()
7. **No emojis in print()** — Windows terminal crashes
8. **Gmail Threading:** Gmail groups same-subject emails. Use `.last` on the `.a3s` body wrapper to get the *newest* email in the thread, not `.first`.
9. **OTP Deletion:** Always click "Delete" on the email after reading the OTP so stale OTPs don't pollute the next run.
10. **Black OTP Screens:** The Saudia app uses `FLAG_SECURE` on the OTP screen, making screenshots black. Rely on Accessibility elements instead.
11. **OTP Field Focus (Far-Left Tap):** The OTP input is a single wide 6-digit box. Tapping the *center* bounds clicks the empty space between digits and fails to focus. Tap `left + 40` pixels to focus the first box.
12. **OTP Retry Logic:** App restart is expensive. If an OTP fails, verify if the OTP screen is still active. If yes, fetch a fresh OTP from Gmail and try again without restarting the app.

---

## Dependencies

```
pip install openpyxl requests playwright
playwright install chromium
```

---

## How to Run

```bash
cd C:\Users\ashus\SaudiaAutomation
python scripts\main.py
```

Pre-requisites:
1. Phone connected, Saudia app installed, Accessibility Service ON
2. Brave browser open with Gmail logged in
3. Excel file at `data\passengers.xlsx`

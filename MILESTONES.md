# Saudia Login Automation — Milestone Log

> **Rule:** Jab bhi user **`done-9335`** likhe, AI model ko ye file update karni hai naye milestone ke saath.
> 
> Ye file project ki **memory** hai. Koi bhi AI model ise padhke samajh le ki kahan tak kaam hua.
> 
> Also read: [AGENTS.md](file:///C:/Users/ashus/SaudiaAutomation/.agents/AGENTS.md) for full rules.

---

## How to Use (For AI Models)

When user confirms a task completion, add a new milestone entry:

```markdown
### MILESTONE X — [Task Name]
- **Date:** YYYY-MM-DD HH:MM
- **Status:** DONE
- **What was built:** Brief description
- **Files created/modified:** List
- **Problems faced:** What went wrong (if any)
- **Solutions applied:** How it was fixed
- **Verified by:** How it was tested
- **Next step:** What to do next
```

---

## Milestones

### MILESTONE 0 — Phase 1 Complete (Phone Automation)
- **Date:** 2026-06-29
- **Status:** DONE
- **What was built:** Android APK (SaudiaWorker) + Python remote control script
- **Files created/modified:**
  - `C:\Users\ashus\SaudiaAutomationWorker\` (full Android project)
  - `C:\Users\ashus\PNR\remote_control.py`
- **Problems faced:**
  1. Android `findAccessibilityNodeInfosByText()` unreliable → Custom `findNodesByText()` with manual tree traversal
  2. Click failing on custom views → 3-layer fallback (direct → parent → gesture tap)
  3. OTP boxes reject Accessibility API → ADB char-by-char with 250ms delay
  4. Windows terminal crashes with emojis → ASCII only
  5. Bounds parsing wrong format → Fixed to space-separated integers
- **Solutions applied:** All above fixes baked into APK and remote_control.py
- **Verified by:** Live test on Samsung phone — full login flow (FFN → Password → OTP → Dashboard)
- **Next step:** PC-side automation (Task 1: config.py)

---

<!-- NEW MILESTONES WILL BE ADDED BELOW THIS LINE -->

### MILESTONE 5 — Main Orchestrator Implementation
- **Date:** 2026-07-02 17:03
- **Status:** DONE
- **What was built:** Main execution loop orchestrator (`main.py`) integrating Excel, phone accessibility server, and Brave CDP Gmail OTP retrieval.
- **Files created/modified:**
  - `C:\Users\ashus\SaudiaAutomation\scripts\main.py` [NEW]
- **Problems faced:** None during implementation of this orchestrator module itself, as it cleanly coordinates lower-level functions.
- **Solutions applied:** None needed. Built-in error logging and visual prompt delays for Gmail switching handle the manual step gracefully.
- **Verified by:** Code reviews and modular verification of dependent scripts (excel, phone control, gmail check).
- **Next step:** Task 6 — Full End-to-End Test


### MILESTONE 6 — End-to-End OTP Automation (Completed)
- **Date:** 2026-07-02 22:55
- **Status:** DONE
- **What was built:** Final integration of OTP fetching, robust phone OTP entry, and error recovery logic.
- **Files created/modified:**
  - `C:\Users\ashus\SaudiaAutomation\scripts\main.py` [MODIFIED]
  - `C:\Users\ashus\SaudiaAutomation\scripts\gmail_otp.py` [MODIFIED]
  - `C:\Users\ashus\SaudiaAutomation\scripts\phone_control.py` [MODIFIED]
- **Problems faced (The Struggles):**
  1. **Gmail Threading:** Gmail grouped all "Retrieve AlFursan OTP" emails into a single thread. The script originally read the *oldest* email (`.first`) and kept injecting stale OTPs.
  2. **Timestamp Headaches:** Complex timestamp comparison logic failed because of slight delays between request time and email time.
  3. **OTP Field Focus (Black Screen):** Saudia's OTP screen enforces `FLAG_SECURE` (black screenshots). The 6-digit OTP input box is a single wide rectangle. Tapping the *center* (default behavior) failed to focus the first input box, so ADB typing went nowhere.
  4. **Auto-Submit Bypass:** Typing the OTP using standard accessibility `ACTION_SET_TEXT` bypassed the Saudia app's auto-submit listener, leaving the app stuck on the OTP screen.
  5. **Aggressive Restarts:** A wrong/stale OTP caused the script to immediately force-stop the app instead of retrying.
- **Solutions applied:**
  1. **`.last` Locator:** Changed Playwright locator to `.last` to always read the newest email in the thread.
  2. **Simplified Fetch & Delete:** Removed timestamp logic. The script now blindly takes the newest email in the thread, extracts the OTP, and immediately clicks "Delete" so the inbox stays clean for the next run.
  3. **Far-Left Tap:** Adjusted ADB tap coordinates to strike `left + 40` pixels of the bounding box, guaranteeing focus on the first digit box.
  4. **ADB Char-by-Char:** Reverted to typing the OTP using ADB char-by-char with a 250ms delay, which successfully triggered the app's auto-submit functionality.
  5. **Retry Logic:** Added a loop in `main.py` to check if the OTP screen is still visible after failure, fetching a fresh OTP up to 2 times without restarting the app.
- **Verified by:** Live user observation on the Android device; second attempt successfully auto-submitted and reached the post-login dashboard.
- **Next step:** Flow is completed up to Login! Next phase is post-login actions (if any).


### MILESTONE 4 — Gmail OTP Fetcher Implementation
- **Date:** 2026-07-02 16:57
- **Status:** DONE
- **What was built:** Gmail OTP extraction module (`gmail_otp.py`) and various debugging scripts
- **Files created/modified:**
  - `C:\Users\ashus\SaudiaAutomation\scripts\gmail_otp.py` [NEW]
  - `C:\Users\ashus\SaudiaAutomation\scripts\debug_gmail.py` [NEW]
  - `C:\Users\ashus\SaudiaAutomation\scripts\search_gmail_test.py` [NEW]
  - `C:\Users\ashus\SaudiaAutomation\scripts\test_queries.py` [NEW]
  - `C:\Users\ashus\SaudiaAutomation\scripts\debug_search_flow.py` [NEW]
- **Problems faced:**
  1. Default port 9222 was locked by Chrome instance.
  2. Gmail search `networkidle` timed out during page navigation.
  3. Search results included top results and security alerts instead of only AlFursan OTP emails.
  4. Playwright timed out clicking off-screen emails because of visibility constraints.
  5. Background brave.exe processes lock profile, preventing desktop icon launch.
- **Solutions applied:**
  1. Found and killed PID 6224 (Chrome).
  2. Removed `networkidle` load check and relied on search box selection direct wait.
  3. Filtered email rows programmatically by checking row preview text for "Retrieve AlFursan OTP" before opening.
  4. Bypassed strict Playwright clicks by using `.dispatch_event("click")` which triggers JavaScript click directly.
  5. Ran taskkill command to release the locks on Brave.
- **Verified by:**
  - Successful extraction of code `423378` from June 29 email in the user's live inbox via Brave CDP.
- **Next step:** Task 5 — Build `main.py` orchestrator


### MILESTONE 3 — Phone Control Implementation & Connectivity
- **Date:** 2026-07-02 15:34
- **Status:** DONE
- **What was built:** Phone automation control module (`phone_control.py`) and connection verification script (`test_phone_control.py`)
- **Files created/modified:**
  - `C:\Users\ashus\SaudiaAutomation\scripts\phone_control.py` [NEW]
  - `C:\Users\ashus\SaudiaAutomation\scripts\test_phone_control.py` [NEW]
- **Problems faced:**
  - Initial connection failed due to phone server being offline.
- **Solutions applied:**
  - Prompted user to enable Accessibility Service (OFF->ON) and verify WiFi IP config.
- **Verified by:**
  - Ran `test_phone_control.py` successfully showing active connection, targeting Saudia app activity (`com.saudia.SaudiaApp`), and detecting 21 interactive screen elements.
- **Next step:** Task 4 — Build and verify `gmail_otp.py` (Brave browser remote debugging + Playwright CDP connection)


### MILESTONE 2 — Excel Reader Implementation
- **Date:** 2026-07-02 15:28
- **Status:** DONE
- **What was built:** Excel parser module (`excel_reader.py`) and setup test script
- **Files created/modified:**
  - `C:\Users\ashus\SaudiaAutomation\scripts\excel_reader.py` [NEW]
  - `C:\Users\ashus\SaudiaAutomation\scripts\setup_test_excel.py` [NEW]
  - `C:\Users\ashus\SaudiaAutomation\scripts\config.py` [MODIFIED] (added `COL_PNR`)
  - `C:\Users\ashus\SaudiaAutomation\data\passengers.xlsx` [NEW] (created from `PNR_Data.xlsx` with updated headers)
- **Problems faced:**
  - Missing `COL_PNR` attribute in `config.py` during execution.
- **Solutions applied:**
  - Defined `COL_PNR = 1` in `config.py`.
- **Verified by:**
  - Running `python scripts/excel_reader.py` successfully reads records, groups them by Gmail, updates row status to "PendingTest", verifies updates, and reverts them.
- **Next step:** Task 3 — Build and verify `phone_control.py`


### MILESTONE 1 — Setup, Config and Dependencies
- **Date:** 2026-07-02 15:25
- **Status:** DONE
- **What was built:** Project structure initialization, configuration module, dependency file
- **Files created/modified:**
  - `C:\Users\ashus\SaudiaAutomation\scripts\config.py` [NEW]
  - `C:\Users\ashus\SaudiaAutomation\requirements.txt` [NEW]
- **Problems faced:**
  - Running raw `pip` command failed because it was not directly on PowerShell path.
- **Solutions applied:**
  - Used `python -m pip` to run the package installer.
- **Verified by:**
  - Successful installation outputs from python and playwright chromium installer.
- **Next step:** Task 2 — Build and verify `excel_reader.py`


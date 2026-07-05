import phone_control

print("\n=== TESTING LOGIN BUTTON CLICK ===")
try:
    print("Checking phone health...")
    if not phone_control.check_health():
        print("Phone not reachable!")
        exit(1)
        
    print("Running login sequence...")
    # This function handles app launch, waiting for tabs, typing, and clicking
    phone_control.login_to_saudia("1006210589", "Hunny@1234")
    print("\nSUCCESS! Login Button was successfully found and hit!")
    
    print("Waiting 10 seconds for OTP screen to load...")
    import time
    time.sleep(10)
    
    print("Dumping OTP screen elements...")
    elements, _ = phone_control.get_screen_elements()
    import json
    with open("otp_screen_elements.json", "w") as f:
        json.dump([e for e in elements if e.get('text') or e.get('content_desc')], f, indent=2)
    print("Saved OTP screen elements to otp_screen_elements.json")
except Exception as e:
    print(f"\nFAILED to click Login button: {e}")


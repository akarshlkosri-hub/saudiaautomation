import phone_control
import sys

print("=== TESTING PHONE CONTROL ===")
print("Checking accessibility server health...")
is_healthy = phone_control.check_health()
print(f"Health check status: {is_healthy}")

if not is_healthy:
    print("WARNING: Phone server is not reachable on port 5000.")
    print("Please make sure the phone is on the same WiFi network and the Accessibility Service is enabled.")
    # We will try to fetch screen elements anyway to see the error
    
print("\nFetching current screen elements...")
elements, activity = phone_control.get_screen_elements()
print(f"Current Activity: {activity}")
print(f"Found {len(elements)} interactive elements on screen.")

if elements:
    print("\nSample Elements (First 5):")
    for i, el in enumerate(elements[:5]):
        print(f"  [{i+1}] Text: {el['text']} | ID: {el['resource_id']} | Class: {el['class']}")
else:
    print("No elements found. (If server is down, this is expected).")

print("\nHealth check test complete.")

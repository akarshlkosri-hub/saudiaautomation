import sys
import os
import json
import phone_control

def main():
    name = sys.argv[1] if len(sys.argv) > 1 else "dump"
    
    # We want it in dumps folder at the project root
    dumps_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "dumps")
    os.makedirs(dumps_dir, exist_ok=True)
    
    # Override screenshot dir temporarily
    phone_control.config.SCREENSHOT_DIR = dumps_dir
    screenshot_path = phone_control.take_screenshot(name)
    
    print(f"Fetching UI hierarchy...")
    elements, activity = phone_control.get_screen_elements()
    
    data = {
        "name": name,
        "activity": activity,
        "elements": elements
    }
    
    json_path = os.path.join(dumps_dir, f"{name}.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        
    print(f"Successfully saved!")
    print(f"Screenshot: {screenshot_path}")
    print(f"JSON Dump: {json_path}")

if __name__ == "__main__":
    main()

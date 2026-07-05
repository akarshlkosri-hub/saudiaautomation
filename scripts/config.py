# Phone connection
DEVICE_IP = "192.168.1.3"
PHONE_PORT = 5000
PHONE_BASE_URL = f"http://{DEVICE_IP}:{PHONE_PORT}"
ADB_PATH = r"C:\Users\ashus\AppData\Local\Android\Sdk\platform-tools\adb.exe"

# Excel
EXCEL_PATH = r"C:\Users\ashus\SaudiaAutomation\data\passenger.xlsx"
COL_PNR = 1         # A (1-indexed for openpyxl)
COL_GMAIL = 4       # D
COL_FFN = 5         # E
COL_PASSWORD = 6    # F
COL_STATUS = 11     # K
COL_REMARKS = 12    # L

# Paths
LOG_DIR = r"C:\Users\ashus\SaudiaAutomation\logs"
SCREENSHOT_DIR = r"C:\Users\ashus\SaudiaAutomation\screenshots"

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

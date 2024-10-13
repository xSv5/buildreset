import ctypes
import time
import win32gui  # To get the window title
import win32api  # To detect key presses
import json  # For working with JSON files
import threading  # For threading support

# Constants for key and mouse events
KEYEVENTF_SCANCODE = 0x0008
KEYEVENTF_KEYUP = 0x0002
INPUT_KEYBOARD = 1
INPUT_MOUSE = 0
MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP = 0x0010
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004

# Virtual key codes for letters A-Z
VK_CODES = {
    'a': 0x41,
    'b': 0x42,
    'c': 0x43,
    'd': 0x44,
    'e': 0x45,
    'f': 0x46,
    'g': 0x47,
    'h': 0x48,
    'i': 0x49,
    'j': 0x4A,
    'k': 0x4B,
    'l': 0x4C,
    'm': 0x4D,
    'n': 0x4E,
    'o': 0x4F,
    'p': 0x50,
    'q': 0x51,
    'r': 0x52,
    's': 0x53,
    't': 0x54,
    'u': 0x55,
    'v': 0x56,
    'w': 0x57,
    'x': 0x58,
    'y': 0x59,
    'z': 0x5A,
}

# Global variables for settings
activator_key = VK_CODES['q']  # Default to 'Q'
edit_key = VK_CODES['f']  # Default to 'F'
reset_key = None  # This will be set dynamically
confirm_edit_key = VK_CODES['f']  # Default to 'F'
press_and_release_delay = 0
delay1 = 0.01
delay2 = 0.01
delay3 = 0.1
delay4 = 0.01

# Structures needed for SendInput
class KEYBDINPUT(ctypes.Structure):
    _fields_ = [("wVk", ctypes.c_ushort),
                ("wScan", ctypes.c_ushort),
                ("dwFlags", ctypes.c_ulong),
                ("time", ctypes.c_ulong),
                ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))]

class MOUSEINPUT(ctypes.Structure):
    _fields_ = [("dx", ctypes.c_long),
                ("dy", ctypes.c_long),
                ("mouseData", ctypes.c_ulong),
                ("dwFlags", ctypes.c_ulong),
                ("time", ctypes.c_ulong),
                ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))]

class INPUT(ctypes.Structure):
    class _INPUT(ctypes.Union):
        _fields_ = [("ki", KEYBDINPUT),
                    ("mi", MOUSEINPUT)]
    _anonymous_ = ("_input",)
    _fields_ = [("type", ctypes.c_ulong),
                ("_input", _INPUT)]

# Global variable to track the buildreset status
buildreset_enabled = False

def press_key(hex_key_code):
    input_structure = INPUT(type=INPUT_KEYBOARD)
    input_structure.ki = KEYBDINPUT(wVk=hex_key_code, wScan=0, dwFlags=0, time=0, dwExtraInfo=None)
    ctypes.windll.user32.SendInput(1, ctypes.pointer(input_structure), ctypes.sizeof(INPUT))

def release_key(hex_key_code):
    input_structure = INPUT(type=INPUT_KEYBOARD)
    input_structure.ki = KEYBDINPUT(wVk=hex_key_code, wScan=0, dwFlags=KEYEVENTF_KEYUP, time=0, dwExtraInfo=None)
    ctypes.windll.user32.SendInput(1, ctypes.pointer(input_structure), ctypes.sizeof(INPUT))

def right_click():
    input_structure = INPUT(type=INPUT_MOUSE)
    input_structure.mi = MOUSEINPUT(dx=0, dy=0, mouseData=0, dwFlags=MOUSEEVENTF_RIGHTDOWN, time=0, dwExtraInfo=None)
    ctypes.windll.user32.SendInput(1, ctypes.pointer(input_structure), ctypes.sizeof(INPUT))

    input_structure.mi.dwFlags = MOUSEEVENTF_RIGHTUP
    ctypes.windll.user32.SendInput(1, ctypes.pointer(input_structure), ctypes.sizeof(INPUT))

def left_click():
    input_structure = INPUT(type=INPUT_MOUSE)
    input_structure.mi = MOUSEINPUT(dx=0, dy=0, mouseData=0, dwFlags=MOUSEEVENTF_LEFTDOWN, time=0, dwExtraInfo=None)
    ctypes.windll.user32.SendInput(1, ctypes.pointer(input_structure), ctypes.sizeof(INPUT))

    input_structure.mi.dwFlags = MOUSEEVENTF_LEFTUP
    ctypes.windll.user32.SendInput(1, ctypes.pointer(input_structure), ctypes.sizeof(INPUT))

def is_fortnite_active():
    active_window_title = win32gui.GetWindowText(win32gui.GetForegroundWindow())
    return "Fortnite" in active_window_title

def load_config():
    global activator_key, edit_key, reset_key, confirm_edit_key
    global press_and_release_delay, delay1, delay2, delay3, delay4
    
    try:
        with open("modules.json", "r") as f:
            config = json.load(f)
            #print("Loaded config:", config)  # Debugging line to show the content of the file
            
            # Ensure it's specifically the buildreset module
            module = config.get("modules", {})
            if module.get("name") == "buildreset":
                #print("Found buildreset module.")  # Debugging line
                
                activator_key_name = module['settings'][0]['activator_key']
                activator_key = VK_CODES.get(activator_key_name, VK_CODES['q'])  # Default to 'Q' if not found
                
                edit_key_name = module['settings'][1]['edit_key']
                edit_key = VK_CODES.get(edit_key_name, VK_CODES['f'])  # Default to 'F' if not found
                
                reset_key_name = module['settings'][2]['reset_key']
                reset_key = reset_key_name  # Keep it as a string for later checking
                
                confirm_edit_key_name = module['settings'][3]['confirm_edit_key']
                confirm_edit_key = VK_CODES.get(confirm_edit_key_name, VK_CODES['f'])  # Default to 'F'
                
                delay1 = float(module['settings'][5]['delay']['delay1'])
                delay2 = float(module['settings'][5]['delay']['delay2'])
                delay3 = float(module['settings'][5]['delay']['delay3'])
                delay4 = float(module['settings'][5]['delay']['delay4'])
            else:
                print("No 'buildreset' module found.")
    except (FileNotFoundError, json.JSONDecodeError):
        print("Error reading modules.json")

def check_buildreset():
    global buildreset_enabled
    while True:
        try:
            with open("data.json", "r") as f:
                data = json.load(f)
                buildreset_enabled = data.get("buildreset", False)
        except (FileNotFoundError, json.JSONDecodeError):
            print("Error reading data.json")
            buildreset_enabled = False

        time.sleep(1)  # Check every second

def check_for_updates():
    while True:
        load_config()  # Reload the configuration every second
        time.sleep(1)  # Sleep for 1 second before checking again

def main():
    load_config()  # Load the configuration at startup
    
    # Start background threads
    threading.Thread(target=check_buildreset, daemon=True).start()
    threading.Thread(target=check_for_updates, daemon=True).start()
    
    print(f"Waiting for '{activator_key}' key press while Fortnite is active...")

    while True:
        if is_fortnite_active() and win32api.GetAsyncKeyState(activator_key) & 0x8000:
            if buildreset_enabled:
                press_key(edit_key)
                release_key(edit_key)
                time.sleep(delay1)
                
                if reset_key == "mouse_left":
                    left_click()
                elif reset_key == "mouse_right":
                    right_click()
                else:
                    print("Invalid reset key configured.")
                
                time.sleep(delay2)
                press_key(edit_key)
                release_key(edit_key)
                time.sleep(delay3)

        time.sleep(delay4)

if __name__ == "__main__":
    main()

import subprocess
import sys
import argparse
import json
import time

# --- Argument parsing ---
parser = argparse.ArgumentParser(description="Dump active window control tree")
parser.add_argument('--debug', action='store_true', help="Enable debug mode and store results in debug.json unless --file is specified")
parser.add_argument('--file', type=str, help="Path to save the JSON file")
parser.add_argument('--mute', action='store_true', help="Mute all console output")
parser.add_argument('--version', action='store_true', help="display tool version")
args = parser.parse_args()

debug, save_file, mute,version = args.debug, args.file, args.mute, args.version

if version:
    print("0.1.2")
    exit()

if mute:
    print = lambda *a, **k: None  # Override print

# --- Ensure required packages ---
def ensure_import(module, pip_name=None):
    try:
        return __import__(module)
    except ImportError:
        pip_name = pip_name or module
        print(f"{module} not found. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", pip_name])
        return __import__(module)

pywinauto = ensure_import("pywinauto")
win32gui = ensure_import("win32gui", "pywin32")
win32con = ensure_import("win32con", "pywin32")
win32process = ensure_import("win32process", "pywin32")
import ctypes
from ctypes import wintypes

# --- Win32 Edit text retrieval ---
def get_edit_text(hwnd):
    user32 = ctypes.windll.user32
    length = user32.SendMessageW(hwnd, win32con.WM_GETTEXTLENGTH, 0, 0)
    if length > 0:
        buf = ctypes.create_unicode_buffer(length + 1)
        user32.SendMessageW(hwnd, win32con.WM_GETTEXT, length + 1, buf)
        return buf.value
    length_a = user32.SendMessageA(hwnd, win32con.WM_GETTEXTLENGTH, 0, 0)
    if length_a > 0:
        buf = ctypes.create_string_buffer(length_a + 1)
        user32.SendMessageA(hwnd, win32con.WM_GETTEXT, length_a + 1, buf)
        return buf.value.decode('mbcs', errors='ignore')
    return ""

# --- Recursive element to dict ---
def element_to_dict(e, depth=0, max_depth=3):
    info = {
        "name": e.window_text(),
        "control_type": e.friendly_class_name(),
        "automation_id": getattr(e.element_info, "automation_id", ""),
        "control_id": getattr(e.element_info, "control_id", None),
        "class_name": getattr(e.element_info, "class_name", None),
        "framework_id": getattr(e.element_info, "framework_id", None),
        "rect": getattr(e.element_info, "rectangle", None).__dict__ if getattr(e.element_info, "rectangle", None) else None,
        "handle": getattr(e.element_info, "handle", None),
        "is_visible": getattr(e.element_info, "visible", None),
        "is_enabled": getattr(e.element_info, "enabled", None),
        "children": []
    }

    hwnd = info["handle"]
    if hwnd:
        try:
            tid, pid = win32process.GetWindowThreadProcessId(hwnd)
            info.update({"process_id": pid, "thread_id": tid})
        except: pass
        try:
            info.update({
                "style": win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE),
                "exstyle": win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
            })
        except: pass

    # --- Text for Edit/Text/Document controls ---
    try:
        if info["control_type"] == "Edit" and hwnd:
            info["text"] = get_edit_text(hwnd)
        elif info["control_type"] in ("Text", "Document"):
            text = e.window_text()
            if text: info["text"] = text
    except: pass

    if depth < max_depth:
        try:
            info["children"] = [element_to_dict(c, depth + 1, max_depth) for c in e.children()]
        except: pass

    return info

if debug:
    print("Waiting 5 seconds to focus on a window...")
    time.sleep(5)
    print("Waiting done scanning...")

# --- Main execution ---
hwnd = win32gui.GetForegroundWindow()
app = pywinauto.Application(backend="uia").connect(handle=hwnd)
window = app.window(handle=hwnd)

if debug and not mute:
    print(f"Active window title: {window.window_text()}")
    window.print_control_identifiers()

tree_dict = element_to_dict(window, max_depth=3)
jtree = json.dumps(tree_dict, indent=2, ensure_ascii=False)
print(jtree)

if debug or save_file:
    path = save_file or "debug.json"
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(jtree)
        print(f"Control tree saved to: {path}")
    except Exception as e:
        print(f"Failed to save file: {e}")



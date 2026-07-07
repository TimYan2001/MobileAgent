import os
import time
import subprocess
from PIL import Image
from time import sleep

def _is_valid_image_file(path):
    try:
        if not os.path.exists(path) or os.path.getsize(path) <= 0:
            return False
        with Image.open(path) as image:
            image.verify()
        return True
    except Exception:
        return False

def _capture_screenshot_png(adb_path, local_file, retries=3):
    if os.path.dirname(local_file) != "":
        os.makedirs(os.path.dirname(local_file), exist_ok=True)

    device_file = "/sdcard/screenshot.png"
    last_error = ""
    for attempt in range(1, retries + 1):
        if os.path.exists(local_file):
            try:
                os.remove(local_file)
            except OSError:
                pass

        subprocess.run(adb_path + f" shell rm {device_file}", capture_output=True, text=True, shell=True)
        time.sleep(0.2)

        result = subprocess.run(
            adb_path + f" shell screencap -p {device_file}",
            capture_output=True,
            text=True,
            shell=True,
        )
        if result.returncode != 0:
            last_error = result.stderr.strip() or result.stdout.strip()
            time.sleep(0.6)
            continue

        result = subprocess.run(
            adb_path + f" pull {device_file} {local_file}",
            capture_output=True,
            text=True,
            shell=True,
        )
        if result.returncode != 0:
            last_error = result.stderr.strip() or result.stdout.strip()
            time.sleep(0.6)
            continue

        if _is_valid_image_file(local_file):
            subprocess.run(adb_path + f" shell rm {device_file}", capture_output=True, text=True, shell=True)
            return local_file

        try:
            size = os.path.getsize(local_file)
        except OSError:
            size = -1
        last_error = f"pulled invalid screenshot file (size={size})"
        print(f"\tScreenshot capture attempt {attempt}/{retries} produced an invalid image; retrying...")
        time.sleep(0.8)

    raise RuntimeError(f"Error: Failed to capture a valid screenshot after {retries} attempts. {last_error}")

def get_screenshot(adb_path):
    image_path = "./screenshot/screenshot.png"
    _capture_screenshot_png(adb_path, image_path, retries=4)
    save_path = "./screenshot/screenshot.jpg"
    image = Image.open(image_path)
    image.convert("RGB").save(save_path, "JPEG")
    os.remove(image_path)

def start_recording(adb_path):
    print("Remove existing screenrecord.mp4")
    command = adb_path + " shell rm /sdcard/screenrecord.mp4"
    subprocess.run(command, capture_output=True, text=True, shell=True)
    print("Start!")
    # Use subprocess.Popen to allow terminating the recording process later
    command = adb_path + " shell screenrecord /sdcard/screenrecord.mp4"
    process = subprocess.Popen(command, shell=True)
    return process

def end_recording(adb_path, output_recording_path):
    print("Stopping recording...")
    # Send SIGINT to stop the screenrecord process gracefully
    stop_command = adb_path + " shell pkill -SIGINT screenrecord"
    subprocess.run(stop_command, capture_output=True, text=True, shell=True)
    sleep(1)  # Allow some time to ensure the recording is stopped
    
    print("Pulling recorded file from device...")
    pull_command = f"{adb_path} pull /sdcard/screenrecord.mp4 {output_recording_path}"
    subprocess.run(pull_command, capture_output=True, text=True, shell=True)
    print(f"Recording saved to {output_recording_path}")


def save_screenshot_to_file(adb_path, file_path="screenshot.png"):
    """
    Captures a screenshot from an Android device using ADB, saves it locally, and removes the screenshot from the device.

    Args:
        adb_path (str): The path to the adb executable.

    Returns:
        str: The path to the saved screenshot, or raises an exception on failure.
    """
    local_file = file_path

    try:
        _capture_screenshot_png(adb_path, local_file, retries=4)
        print(f"\tAtomic Operation Screenshot saved to {local_file}")
        return local_file
    
    except Exception as e:
        print(str(e))
        return None


def tap(adb_path, x, y):
    command = adb_path + f" shell input tap {x} {y}"
    subprocess.run(command, capture_output=True, text=True, shell=True)


def type(adb_path, text):
    text = text.replace("\\n", "_").replace("\n", "_")
    for char in text:
        if char == ' ':
            command = adb_path + f" shell input text %s"
            subprocess.run(command, capture_output=True, text=True, shell=True)
        elif char == '_':
            command = adb_path + f" shell input keyevent 66"
            subprocess.run(command, capture_output=True, text=True, shell=True)
        elif 'a' <= char <= 'z' or 'A' <= char <= 'Z' or char.isdigit():
            command = adb_path + f" shell input text {char}"
            subprocess.run(command, capture_output=True, text=True, shell=True)
        elif char in '-.,!?@\'°/:;()':
            command = adb_path + f" shell input text \"{char}\""
            subprocess.run(command, capture_output=True, text=True, shell=True)
        else:
            command = adb_path + f" shell am broadcast -a ADB_INPUT_TEXT --es msg \"{char}\""
            subprocess.run(command, capture_output=True, text=True, shell=True)

def enter(adb_path):
    command = adb_path + f" shell input keyevent KEYCODE_ENTER"
    subprocess.run(command, capture_output=True, text=True, shell=True)

def swipe(adb_path, x1, y1, x2, y2):
    command = adb_path + f" shell input swipe {x1} {y1} {x2} {y2} 500"
    subprocess.run(command, capture_output=True, text=True, shell=True)


def back(adb_path):
    command = adb_path + f" shell input keyevent 4"
    subprocess.run(command, capture_output=True, text=True, shell=True)
    
    
def home(adb_path):
    # command = adb_path + f" shell am start -a android.intent.action.MAIN -c android.intent.category.HOME"
    command = adb_path + f" shell input keyevent KEYCODE_HOME"
    subprocess.run(command, capture_output=True, text=True, shell=True)

def switch_app(adb_path):
    command = adb_path + f" shell input keyevent KEYCODE_APP_SWITCH"
    subprocess.run(command, capture_output=True, text=True, shell=True)

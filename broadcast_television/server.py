import socket
import cv2
import pickle
import struct
import threading
import sys
from pynput import keyboard

# Global flag to signal all threads to stop
running = True


def on_press(key):
    global running
    if key == keyboard.Key.esc:
        print("[!] Escape key pressed. Shutting down...")
        running = False
        return False  # Stop the listener


def handle_client(client_socket, addr):
    global running
    try:
        while running:
            img, frame = vid.read()
            if not img:
                break
            a = pickle.dumps(frame)
            message = struct.pack("Q", len(a)) + a
            client_socket.sendall(message)
    except (ConnectionResetError, BrokenPipeError):
        print(f"[!] Client {addr} disconnected")
    finally:
        client_socket.close()


server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
host_ip = "192.168.29.122"
port = 6666
socket_address = (host_ip, port)

server_socket.bind(socket_address)
server_socket.listen(5)
print(f"[*] Listening on {socket_address}")
print("[*] Press ESC to shut down the server")

vid = cv2.VideoCapture(0)
vid.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
vid.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

if not vid.isOpened():
    print("[!] Error: Could not open video capture")
    server_socket.close()
    sys.exit(1)

# Start the keyboard listener
listener = keyboard.Listener(on_press=on_press)
listener.start()

try:
    while running:
        server_socket.settimeout(1.0)  # Set a timeout for accept()
        try:
            client_socket, addr = server_socket.accept()
            print(f"[+] Connected: {addr}")
            client_thread = threading.Thread(
                target=handle_client, args=(client_socket, addr)
            )
            client_thread.start()
        except socket.timeout:
            continue
except KeyboardInterrupt:
    print("[!] Keyboard interrupt received")
finally:
    running = False
    print("[*] Shutting down...")
    vid.release()
    server_socket.close()
    cv2.destroyAllWindows()
    sys.exit(0)


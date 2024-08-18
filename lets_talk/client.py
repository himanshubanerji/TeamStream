import socket
import cv2
import pickle
import struct
import sys
from pynput import keyboard

running = True


def on_press(key):
    global running
    if key == keyboard.Key.esc:
        print("[!] Escape key pressed. Shutting down...")
        running = False
        return False  # Stop the listener


def connect_to_server(host_ip, port):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client_socket.connect((host_ip, port))
        return client_socket
    except ConnectionRefusedError:
        print(f"[!] Could not connect to server at {host_ip}:{port}")
        return None


def receive_video_stream(client_socket):
    data = b""
    payload_size = struct.calcsize("Q")
    while running:
        while len(data) < payload_size:
            packet = client_socket.recv(4 * 1024)
            if not packet:
                return
            data += packet
        packed_msg_size = data[:payload_size]
        data = data[payload_size:]
        msg_size = struct.unpack("Q", packed_msg_size)[0]

        while len(data) < msg_size:
            data += client_socket.recv(4 * 1024)
        frame_data = data[:msg_size]
        data = data[msg_size:]
        frame = pickle.loads(frame_data)
        yield frame


def main():
    global running
    host_ip = "127.0.0.1"
    port = 8888

    print("[*] Press ESC to quit the application")

    client_socket = connect_to_server(host_ip, port)
    if not client_socket:
        return

    # Start the keyboard listener
    listener = keyboard.Listener(on_press=on_press)
    listener.start()

    try:
        for frame in receive_video_stream(client_socket):
            cv2.imshow("Live Streaming Video Chat", frame)
            if cv2.waitKey(1) & 0xFF == ord("q") or not running:
                break
    except (ConnectionResetError, struct.error):
        print("[!] Connection to server lost")
    finally:
        running = False
        client_socket.close()
        cv2.destroyAllWindows()
        sys.exit(0)


if __name__ == "__main__":
    main()


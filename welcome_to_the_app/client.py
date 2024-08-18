import socket
import cv2
import pickle
import struct
import threading
import select
import errno
from tkinter import *
from tkinter import scrolledtext
from PIL import Image, ImageTk

HEADER_LENGTH = 10
IP = "127.0.0.1"
VIDEO_PORT = 9988
CHAT_PORT = 6677

running = True

class UsernameDialog:
    def __init__(self, parent):
        self.username = None
        self.top = Toplevel(parent)
        self.top.title("Enter Username")
        self.top.geometry("300x100")
        self.top.protocol("WM_DELETE_WINDOW", self.on_closing)

        Label(self.top, text="Username:").pack()
        self.entry = Entry(self.top)
        self.entry.pack(pady=10)
        self.entry.focus_set()

        Button(self.top, text="OK", command=self.on_ok).pack()

        self.top.bind("<Return>", lambda e: self.on_ok())

    def on_ok(self):
        self.username = self.entry.get()
        self.top.destroy()

    def on_closing(self):
        self.username = None
        self.top.destroy()

class VideoChatApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Group Video Chat")
        self.root.geometry("800x600")

        self.video_label = Label(root, text="Waiting for video connection...", bg="black", fg="white")
        self.video_label.pack(side="top", fill="both", expand=True)

        self.chat_box = scrolledtext.ScrolledText(root, wrap=WORD, height=10)
        self.chat_box.pack(side="left", fill="both", expand=True)
        self.chat_box.insert(END, "Waiting for chat connection...\n")
        self.chat_box.config(state=DISABLED)

        self.message_entry = Entry(root)
        self.message_entry.pack(side="left", fill="x", expand=True)

        self.send_button = Button(root, text="Send", command=self.send_message)
        self.send_button.pack(side="right")

        self.video_thread = None
        self.chat_thread = None
        self.client_socket = None
        self.username = None

    def connect_to_server(self, port):
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            client_socket.connect((IP, port))
            print(f"Connected to server at {IP}:{port}")
            return client_socket
        except ConnectionRefusedError:
            print(f"[!] Could not connect to server at {IP}:{port}")
            return None

    def start_video_stream(self):
        print("Starting video stream...")
        client_socket = self.connect_to_server(VIDEO_PORT)
        if not client_socket:
            self.video_label.config(text="Failed to connect to video server")
            return

        data = b""
        payload_size = struct.calcsize("Q")
        while running:
            try:
                while len(data) < payload_size:
                    packet = client_socket.recv(4 * 1024)
                    if not packet:
                        break
                    data += packet
                packed_msg_size = data[:payload_size]
                data = data[payload_size:]
                msg_size = struct.unpack("Q", packed_msg_size)[0]

                while len(data) < msg_size:
                    data += client_socket.recv(4 * 1024)
                frame_data = data[:msg_size]
                data = data[msg_size:]
                frame = pickle.loads(frame_data)

                cv2_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = cv2.resize(cv2_image, (640, 480))
                img = ImageTk.PhotoImage(image=Image.fromarray(img))
                self.video_label.config(image=img)
                self.video_label.image = img
            except Exception as e:
                print(f"Error in video stream: {e}")
                break

        print("Video stream ended")
        self.video_label.config(text="Video stream disconnected")

    def start_chat(self):
        print("Starting chat...")
        self.client_socket = self.connect_to_server(CHAT_PORT)
        if not self.client_socket:
            self.update_chat_box("Failed to connect to chat server\n")
            return

        self.client_socket.setblocking(False)
        
        dialog = UsernameDialog(self.root)
        self.root.wait_window(dialog.top)
        self.username = dialog.username

        if not self.username:
            self.update_chat_box("Username is required. Chat disconnected.\n")
            return

        username_header = f"{len(self.username):<{HEADER_LENGTH}}".encode('utf-8')
        self.client_socket.send(username_header + self.username.encode('utf-8'))

        while running:
            try:
                while True:
                    username_header = self.client_socket.recv(HEADER_LENGTH)
                    if not len(username_header):
                        print('Connection closed by the server')
                        return

                    username_length = int(username_header.decode('utf-8').strip())
                    username = self.client_socket.recv(username_length).decode('utf-8')
                    message_header = self.client_socket.recv(HEADER_LENGTH)
                    message_length = int(message_header.decode('utf-8').strip())
                    message = self.client_socket.recv(message_length).decode('utf-8')
                    self.update_chat_box(f'{username} > {message}\n')

            except IOError as e:
                if e.errno != errno.EAGAIN and e.errno != errno.EWOULDBLOCK:
                    print('Reading error: {}'.format(str(e)))
                    break
                continue
            except Exception as e:
                print('Reading error: '.format(str(e)))
                break

        print("Chat ended")
        self.update_chat_box("Chat disconnected\n")

    def update_chat_box(self, message):
        self.chat_box.config(state=NORMAL)
        self.chat_box.insert(END, message)
        self.chat_box.yview(END)
        self.chat_box.config(state=DISABLED)

    def send_message(self):
        if self.client_socket and self.username:
            message = self.message_entry.get()
            if message:
                message = message.encode('utf-8')
                message_header = f"{len(message):<{HEADER_LENGTH}}".encode('utf-8')
                self.client_socket.send(message_header + message)
                self.update_chat_box(f'You > {self.message_entry.get()}\n')
                self.message_entry.delete(0, END)
        else:
            self.update_chat_box("Not connected to chat server or username not set\n")

    def run(self):
        print("Starting application...")
        self.chat_thread = threading.Thread(target=self.start_chat)
        self.chat_thread.start()
        
        self.video_thread = threading.Thread(target=self.start_video_stream)
        self.video_thread.start()
        
        print("Entering main loop...")
        self.root.mainloop()
        print("Main loop exited.")

if __name__ == "__main__":
    print("Initializing Tkinter...")
    root = Tk()
    print("Creating VideoChatApp...")
    app = VideoChatApp(root)
    print("Running application...")
    app.run()
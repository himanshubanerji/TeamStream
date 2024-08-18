import socket
import cv2
import pickle
import struct
import threading
import select

HEADER_LENGTH = 10
IP = "127.0.0.1"
VIDEO_PORT = 9988
CHAT_PORT = 6677

# Global variables
clients = {}  # For chat
sockets_list = []  # List of chat client sockets
running = True

# Video handling
def handle_video_client(client_socket):
    vid = cv2.VideoCapture(0)
    vid.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    vid.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    while running:
        img, frame = vid.read()
        if not img:
            break
        a = pickle.dumps(frame)
        message = struct.pack("Q", len(a)) + a
        try:
            client_socket.sendall(message)
        except:
            break

    client_socket.close()
    vid.release()

# Chat handling
def receive_message(client_socket):
    try:
        message_header = client_socket.recv(HEADER_LENGTH)
        if not len(message_header):
            return False
        message_length = int(message_header.decode('utf-8').strip())
        return {'header': message_header, 'data': client_socket.recv(message_length)}
    except:
        return False

def handle_chat_client(server_socket):
    while True:
        read_sockets, _, exception_sockets = select.select(sockets_list, [], sockets_list)
        for notified_socket in read_sockets:
            if notified_socket == server_socket:
                client_socket, client_address = server_socket.accept()
                user = receive_message(client_socket)
                if user is False:
                    continue
                sockets_list.append(client_socket)
                clients[client_socket] = user
                print(f"Accepted new connection from {client_address[0]}:{client_address[1]}, username: {user['data'].decode('utf-8')}")
            else:
                message = receive_message(notified_socket)
                if message is False:
                    print(f"Closed connection from: {clients[notified_socket]['data'].decode('utf-8')}")
                    sockets_list.remove(notified_socket)
                    del clients[notified_socket]
                    continue
                user = clients[notified_socket]
                print(f"Received message from {user['data'].decode('utf-8')}: {message['data'].decode('utf-8')}")
                for client_socket in clients:
                    if client_socket != notified_socket:
                        client_socket.send(user['header'] + user['data'] + message['header'] + message['data'])

        for notified_socket in exception_sockets:
            sockets_list.remove(notified_socket)
            del clients[notified_socket]

# Main server setup
def start_server():
    # Video socket
    video_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    video_socket.bind((IP, VIDEO_PORT))
    video_socket.listen(5)
    print(f"[*] Video server listening on {IP}:{VIDEO_PORT}")

    # Chat socket
    chat_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    chat_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    chat_socket.bind((IP, CHAT_PORT))
    chat_socket.listen()
    sockets_list.append(chat_socket)
    print(f"[*] Chat server listening on {IP}:{CHAT_PORT}")

    video_thread = threading.Thread(target=handle_video_client, args=(video_socket.accept()[0],))
    video_thread.start()

    chat_thread = threading.Thread(target=handle_chat_client, args=(chat_socket,))
    chat_thread.start()

if __name__ == "__main__":
    start_server()

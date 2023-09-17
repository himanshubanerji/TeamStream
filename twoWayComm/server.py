import socket
import cv2
import pickle
import struct

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

host_ip = '192.168.29.122'
print('[+] Connecting to : ', host_ip)
port = 9988
socket_address = (host_ip, port)

server_socket.bind(socket_address)

server_socket.listen(5)
print("[*] Listening as : ", socket_address)

while True:
    client_socket, addr = server_socket.accept()
    print('[+] Connected:', addr)
    if client_socket:
        vid = cv2.VideoCapture(0)
        vid.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        vid.set(cv2.CAP_PROP_FRAME_HEIGHT, 500)
        while (vid.isOpened()):
            img, frame = vid.read()
            a = pickle.dumps(frame)
            message = struct.pack("Q", len(a)) + a
            client_socket.sendall(message)
            cv2.imshow("Sender's Video", frame)
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                client_socket.close()

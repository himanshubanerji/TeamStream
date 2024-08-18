import socket
import os
import cv2
import pickle
import threading
import struct


def sendImage():
    os.system('python3 server.py')


t1 = threading.Thread(target=sendImage)
t1.start()

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
host_ip = '192.168.29.24'
port = 8888
client_socket.connect((host_ip, port))
data = b""
payload_size = struct.calcsize("Q")
while True:
    while len(data) < payload_size:
        packet = client_socket.recv(8 * 1024)
        if not packet: break
        data += packet
    packed_msg_size = data[:payload_size]
    data = data[payload_size:]
    msg_size = struct.unpack("Q", packed_msg_size)[0]

    while len(data) < msg_size:
        data += client_socket.recv(8 * 1024)
    frame_data = data[:msg_size]
    data = data[msg_size:]
    frame = pickle.loads(frame_data)
    cv2.imshow("Live Streaming Video Chat", frame)
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break
client_socket.close()





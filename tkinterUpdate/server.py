import socket
import cv2
import pickle
import struct
import pyaudio
import threading

CHUNK = 1024
WIDTH = 2
CHANNELS = 2
RATE = 44100
FORMAT = pyaudio.paInt16

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
host_name = socket.gethostname()
host_ip = socket.gethostbyname(host_name)
print('HOST IP:', host_ip)
port = 9999
socket_address = (host_ip, port)

server_socket.bind(socket_address)
server_socket.listen(5)
print("LISTENING AT:", socket_address)

audio = pyaudio.PyAudio()
stream = audio.open(format=FORMAT, channels=CHANNELS,
                    rate=RATE, input=True,
                    frames_per_buffer=CHUNK)

client_socket, addr = server_socket.accept()
print('GOT CONNECTION FROM:', addr)

def video_stream():
    vid = cv2.VideoCapture(0)
    while vid.isOpened():
        img, frame = vid.read()
        a = pickle.dumps(frame)
        message = struct.pack("Q", len(a)) + a
        client_socket.sendall(message)

def audio_stream():
    while True:
        data = stream.read(CHUNK)
        client_socket.sendall(data)

threading.Thread(target=video_stream).start()
threading.Thread(target=audio_stream).start()

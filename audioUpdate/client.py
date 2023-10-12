import socket
import cv2
import pickle
import struct
import threading
import pyaudio


def sendAudio(audio_format, channels, rate, chunk):
    stream_send = p.open(format=audio_format, channels=channels, rate=rate, input=True, frames_per_buffer=chunk)
    while True:
        try:
            data = stream_send.read(chunk)
            client_socket.sendall(data)
        except:
            break


def receiveAudio(audio_format, channels, rate, chunk):
    stream_receive = p.open(format=audio_format, channels=channels, rate=rate, output=True, frames_per_buffer=chunk)
    while True:
        try:
            data = client_socket.recv(chunk)
            if not data:
                break
            stream_receive.write(data, chunk)
        except:
            break


host_ip = '192.168.29.122'
port = 9999
audio_format = pyaudio.paInt16
channels = 2
rate = 44100
chunk = 1024
payload_size = struct.calcsize("Q")

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((host_ip, port))
data_buffer = b""

p = pyaudio.PyAudio()

t2 = threading.Thread(target=sendAudio, args=(audio_format, channels, rate, chunk))
t2.start()

t3 = threading.Thread(target=receiveAudio, args=(audio_format, channels, rate, chunk))
t3.start()

try:
    while True:
        while len(data_buffer) < payload_size:
            packet = client_socket.recv(8 * 1024)
            if not packet:
                break
            data_buffer += packet

        packed_msg_size = data_buffer[:payload_size]
        data_buffer = data_buffer[payload_size:]
        msg_size = struct.unpack("Q", packed_msg_size)[0]

        while len(data_buffer) < msg_size:
            data_buffer += client_socket.recv(8 * 1024)
        frame_data = data_buffer[:msg_size]
        data_buffer = data_buffer[msg_size:]
        frame = pickle.loads(frame_data)
        cv2.imshow("RECEIVING VIDEO", frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
finally:
    client_socket.close()
    p.terminate()

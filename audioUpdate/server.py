import socket
import cv2
import pickle
import struct
import threading
import pyaudio
import imutils


def sendAudio(client_socket, audio_format, channels, rate, chunk):
    stream_send = p.open(format=audio_format, channels=channels, rate=rate, input=True, frames_per_buffer=chunk)
    while True:
        try:
            data = stream_send.read(chunk)
            client_socket.sendall(data)
        except:
            break


def receiveAudio(client_socket, audio_format, channels, rate, chunk):
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
socket_address = (host_ip, port)
audio_format = pyaudio.paInt16
channels = 2
rate = 44100
chunk = 1024

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind(socket_address)
server_socket.listen(5)
print("[*] LISTENING AT:", socket_address)

p = pyaudio.PyAudio()

try:
    while True:
        client_socket, addr = server_socket.accept()
        print('[+] CONNECTED FROM:', addr)

        if client_socket:
            vid = cv2.VideoCapture(0)

            t_audio_send = threading.Thread(target=sendAudio, args=(client_socket, audio_format, channels, rate, chunk))
            t_audio_send.start()

            t_audio_receive = threading.Thread(target=receiveAudio, args=(client_socket, audio_format, channels, rate, chunk))
            t_audio_receive.start()

            while vid.isOpened():
                try:
                    ret, frame = vid.read()
                    frame = imutils.resize(frame, width=320)
                    serialized_frame = pickle.dumps(frame)
                    message = struct.pack("Q", len(serialized_frame)) + serialized_frame
                    client_socket.sendall(message)

                    cv2.imshow("SENDER'S VIDEO", frame)
                    key = cv2.waitKey(1) & 0xFF
                    if key == ord('q'):
                        client_socket.close()
                        vid.release()
                        cv2.destroyAllWindows()
                        break
                except:
                    break

except KeyboardInterrupt:
    server_socket.close()
    p.terminate()

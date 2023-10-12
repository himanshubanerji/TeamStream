import socket, cv2, pickle, struct, imutils, threading, pyaudio

#Socket Creation
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
host_name = socket.gethostname()
host_ip = socket.gethostbyname(host_name)
print('HOST IP: ', host_ip)

host_ip = '192.168.29.122'
port = 9999
socket_address = (host_ip, port)

#Socket Bind
server_socket.bind(socket_address)

#Socket Listen
server_socket.listen(5)
print("[*] LISTENING AT: ", socket_address)

# Audio setup
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 2
RATE = 44100

p = pyaudio.PyAudio()

def sendAudio(client_socket):
    stream_send = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
    while True:
        data = stream_send.read(CHUNK)
        client_socket.sendall(data)

def receiveAudio(client_socket):
    stream_receive = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, output=True, frames_per_buffer=CHUNK)
    while True:
        data = client_socket.recv(CHUNK)
        stream_receive.write(data, CHUNK)

#Socket Accept
while True:
    client_socket, addr = server_socket.accept()
    print('[+] CONNECTED FROM: ', addr)
    
    if client_socket:
        vid = cv2.VideoCapture(0)

        t_audio_send = threading.Thread(target=sendAudio, args=(client_socket,))
        t_audio_send.start()

        t_audio_receive = threading.Thread(target=receiveAudio, args=(client_socket,))
        t_audio_receive.start()

        while(vid.isOpened()):
            img, frame = vid.read()
            frame = imutils.resize(frame,width = 320)
            a = pickle.dumps(frame)
            message = struct.pack("Q", len(a)) + a
            client_socket.sendall(message)

            cv2.imshow("SENDER'S VIDEO", frame)
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                client_socket.close()

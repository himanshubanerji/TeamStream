import socket, cv2, pickle, struct, threading, pyaudio

# Create Socket
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
host_ip = '192.168.29.122'
port = 9999
client_socket.connect((host_ip, port))
data = b""
payload_size = struct.calcsize("Q")

# Audio setup
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 2
RATE = 44100

p = pyaudio.PyAudio()

def sendAudio():
    stream_send = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
    while True:
        try:
            data = stream_send.read(CHUNK)
            client_socket.sendall(data)
        except:
            break

def receiveAudio():
    stream_receive = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, output=True, frames_per_buffer=CHUNK)
    while True:
        try:
            data = client_socket.recv(CHUNK)
            if not data:
                break
            stream_receive.write(data, CHUNK)
        except:
            break

t2 = threading.Thread(target=sendAudio)
t2.start()

t3 = threading.Thread(target=receiveAudio)
t3.start()

try:
    while True:
        try:
            while len(data) < payload_size:
                packet = client_socket.recv(8 * 1024)
                if not packet: 
                    break
                data += packet
            packed_msg_size = data[:payload_size]
            data = data[payload_size:]
            msg_size = struct.unpack("Q", packed_msg_size)[0]

            while len(data) < msg_size:
                data += client_socket.recv(8 * 1024)
            frame_data = data[:msg_size]
            data = data[msg_size:]
            frame = pickle.loads(frame_data)
            cv2.imshow("RECEVING VIDEO ", frame)
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
        except:
            break
finally:
    client_socket.close()
    p.terminate()

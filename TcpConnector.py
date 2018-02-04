import socket
import struct
import threading
import queue
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
from Crypto.Hash import SHA256
from base64 import b64encode, b64decode
from io import StringIO

CONTROLLER_PUB_KEY_PATH = "keys/controller.pub.pem"
DRONE_PRIV_KEY_PATH = "keys/drone.priv.pem"

HOSTNAME = "lht.no-ip.biz"
PORT = 5050

MSG_START = "-----BEGIN MESSAGE-----"
MSG_END = "-----END MESSAGE-----"
SIG_START = "-----BEGIN SIGNATURE-----"
SIG_END = "-----END SIGNATURE-----"
NEWLINE = "\n"


def signAndEncode(data: bytes) -> str:
    key = open(DRONE_PRIV_KEY_PATH, "r").read()
    rsakey = RSA.importKey(key)
    signer = PKCS1_v1_5.new(rsakey)
    digest = SHA256.new()
    digest.update(data)
    sign = signer.sign(digest)
    encoded_signature = b64encode(sign).decode()

    return MSG_START + NEWLINE + b64encode(
        data).decode() + NEWLINE + MSG_END + NEWLINE + SIG_START + NEWLINE + encoded_signature + NEWLINE + SIG_END + NEWLINE


def verifyAndDecode(message: str) -> bytes:
    parts = message.split(NEWLINE)
    # Make sure it's well-formed
    if (len(parts) == 6 and parts[0] == MSG_START and parts[2] == MSG_END and parts[3] == SIG_START and parts[
        5] == SIG_END):
        msg = b64decode(parts[1])
        sig = b64decode(parts[4])

        key = open(CONTROLLER_PUB_KEY_PATH, "r").read()
        rsakey = RSA.importKey(key)
        verifier = PKCS1_v1_5.new(rsakey)
        digest = SHA256.new()
        digest.update(msg)
        if(verifier.verify(digest, sig)):
            return msg
        else:
            raise Exception("Verification failed!")
    else:
        raise SyntaxError("Malformed messsage!")


class SenderThread(threading.Thread):
    def __init__(self, send_queue):
        super(SenderThread, self).__init__()
        self.send_queue = send_queue
        self.socket = None
        self.alive = threading.Event()
        self.alive.set()

    def run(self):
        while self.alive.isSet():
            try:
                # Queue.get with timeout to allow checking self.alive
                data = self.send_queue.get(True, 0.1)
                signed = signAndEncode(data)
                self.socket.sendall(signed.encode())
                del data
            except queue.Empty as e:
                continue

    def join(self, timeout=None):
        print("TCP Sender exiting…")
        self.alive.clear()
        threading.Thread.join(self, timeout)

class SocketClientThread(threading.Thread):

    def __init__(self):
        super(SocketClientThread, self).__init__()
        self.send_queue = queue.Queue()
        self.senderThread = SenderThread(self.send_queue)
        self.alive = threading.Event()
        self.alive.set()
        self.socket = None

    def connect(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((HOSTNAME, PORT))
        timeval = struct.pack('ll', 0, 100000)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVTIMEO, timeval)
        self.senderThread.socket = self.socket

    def readline(self):
        recv_buf = StringIO(2048)
        while self.alive.isSet():
            data = self.socket.recv()  # Pull what it can
            recv_buf.write(data)  # Append that segment to the buffer
            if '\n' in data:
                return recv_buf.getvalue().splitlines()[0]

    def run(self):
        self.connect()
        self.senderThread.start()
        while self.alive.isSet():
            try:
                fp = self.socket.makefile()
                while self.alive.isSet():
                    received = fp.readline()
                    if(received == MSG_START):
                        received += NEWLINE
                        for i in range(5):
                            received += fp.readline()
                            received += NEWLINE
                        try:
                            data = verifyAndDecode(received)
                            pass
                        finally:
                            pass
            except Exception as e:
                raise e

    def join(self, timeout=None):
        print("TCP receiver exiting…")
        if(self.senderThread.is_alive()):
            self.senderThread.join(timeout)
        self.alive.clear()
        self.socket.close()
        threading.Thread.join(self, timeout)
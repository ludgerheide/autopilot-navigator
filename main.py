import posix_ipc
from posix_ipc import MessageQueue
from typing import Tuple
import signal
import sys
from DecodedMessage import DecodedMessage
from TcpConnector import SocketClientThread
import time
from TcpConnector import verifyAndDecode, signAndEncode

def signal_handler(_, __):
    print('You pressed Ctrl+C!')
    try:
        tcp_connector.join()
    except Exception as e:
        print("error ending tcp thread!")

    try:
        recv_q.close()
    except Exception as e:
        print("error closing recv queue!")

    try:
        send_q.close()
    except Exception as e:
        print("error closing send queue!")

    sys.exit(0)

def init_queues() -> Tuple[MessageQueue, MessageQueue]:
    RECV_QUEUE_NAME = "/navQueue-fromFlightController"
    SEND_QUEUE_NAME = "/navQueue-toFlightController"

    recv_queue = MessageQueue(RECV_QUEUE_NAME, write=False, read=True)
    send_queue = MessageQueue(SEND_QUEUE_NAME, write=True, read=False)
    return recv_queue, send_queue

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    recv_q, send_q = init_queues()
    tcp_connector = SocketClientThread()
    tcp_connector.start()
    while True:
        try:
            data, _ = recv_q.receive()
            msg = DecodedMessage(data)
        except posix_ipc.ExistentialError as e:
            #Sleep here for a bit so we don't get an infinite amoutn of broken decodes on the closed queue
            print("Queue is gone: " + str(e))
            sys.exit(0)
        except Exception as e:
            print("Receiving/decoding failed with {}".format(str(e)))
            msg = None
        if(msg is not None):
            tcp_connector.send_queue.put(msg.encode())

import posix_ipc
from posix_ipc import MessageQueue
from typing import Tuple
import signal
import sys
from Message import DecodedMessage
from InternetComms import SocketClientThread
import syslog
import time
from InternetComms import verifyAndDecode, signAndEncode
from SimulatedSerialConnector import SimulatedSerialConnector
from Subprograms import SerialConnector, VideoRecorder
from navigation.NavigationThread import NavigationThread
from navigation.Navigators import SimpleRouteFollowingNavigator

TCP_UPDATE_INTERVAL = 2
SIMULATED = False

def quit_handler(_, __):
    '''
    Handles trhe quit signal for an ordinary shutdown. Shuts down the following external services:
    - serialConnector C program
    - video recording and streaming
    And the following internal components
    - TCP position sender
    - POSIX message queues

    :return: Nothing
    '''
    print('You pressed Ctrl+C!')
    try:
        serial_connector.quit()
    except Exception as e:
        print("error closing serial connector!")

    try:
        video_recorder.quit()
    except Exception as e:
        print("error closing video recorder!")

    try:
        tcp_connector.join()
    except Exception as e:
        print("error closing tcp!")

    try:
        navigation_thread.join()
    except Exception as e:
        print("error closing nav!")

    sys.exit(0)

def reload_handler(_, __):
    '''
    Handles the SIGHUP signal for reloading the state. Restarts the external components
    - video recording
    Reloads
    - serialConnector C program
    :return:  nothing
    '''
    syslog.syslog(syslog.LOG_INFO, "TODO: Reloading navigator")
    video_recorder.restart()
    serial_connector.reload()

def init_queue() -> MessageQueue:
    RECV_QUEUE_NAME = "/navQueue-fromFlightController"

    try:
        recv_queue = MessageQueue(RECV_QUEUE_NAME, write=False, read=True)
    except posix_ipc.ExistentialError:
        recv_queue = MessageQueue(RECV_QUEUE_NAME, posix_ipc.O_CREAT, write=False, read=True)

    return recv_queue

if __name__ == "__main__":
    #Set up the signal handlers, queues, threads and subprocesses
    signal.signal(signal.SIGINT, quit_handler)
    signal.signal(signal.SIGTERM, quit_handler)
    signal.signal(signal.SIGHUP, reload_handler)

    recv_q = init_queue()

    tcp_connector = SocketClientThread()
    tcp_connector.start()

    if SIMULATED:
        serial_connector = SimulatedSerialConnector()
        navigator = SimpleRouteFollowingNavigator("Untitled.gpx")
    else:
        #serial_connector = SerialConnector()
        time.sleep(1)
        video_recorder = VideoRecorder()
        navigator = SimpleRouteFollowingNavigator("Untitled.gpx")

    navigation_thread = NavigationThread(navigator)
    navigation_thread.start()

    last_tcp_update = time.time()

    while True:
        try:
            data, _ = recv_q.receive()
            msg = DecodedMessage(data)
        except posix_ipc.ExistentialError as e:
            #Sleep here for a bit so we don't get an infinite amoutn of broken decodes on the closed queue
            print("Queue is gone: " + str(e))
            sys.exit(0)
        except posix_ipc.SignalError as e:
            break
        except Exception as e:
            print("Receiving/decoding failed with {}".format(str(e)))
            msg = None
        if(msg is not None):
            if (time.time() - last_tcp_update > TCP_UPDATE_INTERVAL):
                last_tcp_update = time.time()
                tcp_connector.send_queue.put(msg.encode())
            navigator.update_from_flight_controller(msg)

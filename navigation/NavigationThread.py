import threading
import time
from posix_ipc import MessageQueue

from navigation.Navigators import AbstractNavigator


class NavigationThread(threading.Thread):
    _SEND_QUEUE_NAME = "/navQueue-toFlightController"

    def __init__(self, navigator: AbstractNavigator):
        super(NavigationThread, self).__init__()

        self.send_queue = MessageQueue(self._SEND_QUEUE_NAME, write=True, read=False)

        self.last_update = time.time()
        self.navigator = navigator

        self.alive = threading.Event()
        self.alive.set()

    def run(self):
        while self.alive.isSet():
            msg = self.navigator.get_command_update()
            if msg is not None:
                data = msg.SerializeToString()
                try:
                    self.send_queue.send(data, 1.0)
                except Exception as e:
                    print(e)
            time.sleep(0.5)

    def join(self, timeout=None):
        print("Navigation Thread exiting…")
        try:
            self.send_queue.close()
        except Exception as e:
            print("error closing recv queue!")
        self.alive.clear()
        threading.Thread.join(self, timeout)



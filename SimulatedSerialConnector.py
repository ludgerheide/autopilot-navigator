import random
import threading
import time
from typing import Tuple, NamedTuple
import posix_ipc
from posix_ipc import MessageQueue

from geographiclib.geodesic import Geodesic

from Subprograms import SerialConnector
from communicationProtocol_pb2 import DroneMessage

class SimulatedSerialConnector(SerialConnector):

    def __init__(self):
        self.thread = SimulatorThread()
        self.thread.start()

    def reload(self):
        self.thread.join()
        self.thread = SimulatorThread()
        self.thread.start()


    def quit(self):
        self.thread.join()

class SimulatorThread(threading.Thread):
    _DEFAULT_POSITION = (52.5005, 13.1692)

    def __init__(self):
        super(SimulatorThread, self).__init__()

        self.position = self._DEFAULT_POSITION
        self.heading = 0
        self.speed = 0
        self.altitude = 0

        self.target_altitude = 100
        self.target_heading = 0
        self.target_speed = 10

        self.start_time = time.time()

        self.recv_queue, self.send_queue = self.init_queues()
        self.alive = threading.Event()
        self.alive.set()

    def init_queues(self) -> Tuple[MessageQueue, MessageQueue]:
        RECV_QUEUE_NAME = "/navQueue-toFlightController"
        SEND_QUEUE_NAME = "/navQueue-fromFlightController"

        recv_queue = MessageQueue(RECV_QUEUE_NAME, write=False, read=True)
        send_queue = MessageQueue(SEND_QUEUE_NAME, write=True, read=False)
        return recv_queue, send_queue

    def run(self):
        self.last_update = time.time()
        while self.alive.isSet():
            try:
                command, _ = self.recv_queue.receive(0.1)
                msg = DroneMessage()
                msg.ParseFromString(command)
                self.target_altitude = msg.input_command.altitude/100
                self.target_heading = msg.input_command.heading/64
                if(self.target_heading) < 0:
                    self.target_heading+=360
                self.target_speed = msg.input_command.speed/100
            except posix_ipc.BusyError:
                pass

            if (time.time() - self.last_update) > 0.5:

                # Calculate and send an update
                self.calculate_update()
                self.send_update()

    def calculate_update(self):
        dt = time.time() - self.last_update
        self.last_update = time.time()

        ds = self.target_speed*dt

        result = Geodesic.WGS84.Direct(self.position[0], self.position[1], self.heading, ds)

        self.position = (result["lat2"], result["lon2"])
        self.heading = self.target_heading
        self.altitude = self.target_altitude



    def send_update(self):
        timestamp = int((time.time()- self.start_time) * 1000000)

        msg = DroneMessage()
        msg.current_mode = DroneMessage.FlightMode.Value('m_flybywire')
        msg.timestamp = timestamp

        msg.current_position.timestamp = timestamp
        msg.current_position.latitude = self.position[0]
        msg.current_position.longitude = self.position[1]

        msg.current_groundspeed.timestamp = timestamp
        msg.current_groundspeed.speed = int(self.speed*100)
        msg.current_groundspeed.course_over_ground = int(self.heading*64)

        msg.current_altitude.timestamp = timestamp
        msg.current_altitude.altitude = int(self.altitude*100)

        data = msg.SerializeToString()

        self.send_queue.send(data)

    def join(self, timeout=None):
        print("Simulator exiting…")
        try:
            self.recv_queue.close()
        except Exception as e:
            print("error closing recv queue!")

        try:
            self.send_queue.close()
        except Exception as e:
            print("error closing send queue!")

        self.alive.clear()
        threading.Thread.join(self, timeout)
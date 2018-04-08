import time
from abc import ABC, abstractmethod
import typing

from geographiclib.geodesic import Geodesic

from Message import DecodedMessage
from communicationProtocol_pb2 import Route, DroneMessage, Waypoint as ProtoWp
from typing import NamedTuple
import gpxpy.parser
from multiprocessing import Lock

from navigation.Waypoint import Waypoint


class AbstractNavigator(ABC):
    @abstractmethod
    def update_from_base(self, update):
        pass

    @abstractmethod
    def update_from_flight_controller(self, update: DroneMessage):
        pass

    @abstractmethod
    def get_command_update(self) -> DroneMessage:
        pass

class SimpleRouteFollowingNavigator(AbstractNavigator):
    '''
    Simply follows a GPX route by making a heading towards the next waypoint until we are <100m to it.
    Once we reach the last waypoint, circle back
    '''
    def __init__(self, gpx_file):
        gpx_file = open(gpx_file, 'r')
        gpx_parser = gpxpy.parser.GPXParser(gpx_file)
        gpx_parser.parse()

        self.route = list()
        for point in gpx_parser.gpx.routes[0].points:
            wp = Waypoint()
            wp.set_latlon(point.latitude, point.longitude, 0, 0)
            self.route.append(wp)
        self.current_target_index = 0

        self.lock = Lock()

        self.last_update = None
        self.latitude = None
        self.longitude = None


    def update_from_base(self, update: Route):
        assert isinstance(update, Route)
        self.route = list()
        for protowp in Route.routes:
            self.route.append()

    def update_from_flight_controller(self, update: DecodedMessage):
        with self.lock:
            # We have received an update from the flight controller. In this simple parser, simply get current latlon and
            # save it
            self.last_update = time.time()
            self.latitude = update.latitude
            self.longitude = update.longitude

            #Check if we are close enough to the target to move to the next one
            goal_lat = self.route[self.current_target_index].latitude
            goal_lon = self.route[self.current_target_index].longitude
            result = Geodesic.WGS84.Inverse(self.latitude, self.longitude, goal_lat, goal_lon, outmask=Geodesic.DISTANCE)
            distance = result["s12"]
            if distance < 100:
                if self.current_target_index < (len(self.route) - 1):
                    self.current_target_index += 1
                else:
                    self.current_target_index = 0

    def get_command_update(self):
        with self.lock:
            #We should send an update to the aircraft. In this simple parser, simply claculate the beating towards the goal poinz
            if self.latitude is not None and self.longitude is not None and (time.time() - self.last_update) < 60.0:
                goal_lat = self.route[self.current_target_index].latitude
                goal_lon = self.route[self.current_target_index].longitude
                result = Geodesic.WGS84.Inverse(self.latitude, self.longitude, goal_lat, goal_lon, outmask=Geodesic.AZIMUTH)

                msg = DroneMessage()

                msg.input_command.altitude = 100*100 #100 m
                msg.input_command.heading = int(result['azi1']*64)
                msg.input_command.speed = 10*100 #10 m/s

                return msg
            else:
                return None



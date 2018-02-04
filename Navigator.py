from abc import ABC, abstractmethod
import typing
from communicationProtocol_pb2 import Route, DroneMessage, Waypoint as ProtoWp
from typing import NamedTuple

class AbstractNavigator(ABC):
    @abstractmethod
    def update_from_base(self, update):
        pass

    @abstractmethod
    def update_from_flight_controller(self, update: DroneMessage):
        pass

    @abstractmethod
    def get_command_update(self):
        pass

class Waypoint():
    def __init__(self):
        self.latitude = 0
        self.longitude = 0
        self.altitude = 0

        self.orbit_radius = 0
        self.orbit_until_target_altitude = False
        self.orbit_clockwise = False

    def __init__(self, lat, lon, alt, orbit_radius, orbit_until_target_altitude=False, orbit_clockwise=False):
        self.latitude = lat
        self.longitude = lon
        self.altitude = alt

        self.orbit_radius = orbit_radius
        self.orbit_until_target_altitude = orbit_until_target_altitude
        self.orbit_clockwise = orbit_clockwise

    def __init__(self, wp: ProtoWp):
        self.latitude = wp.latitude
        self.longitude = wp.longitude
        self.altitude = wp.altitude

        assert wp.orbit_radius is not None
        self.orbit_radius = wp.orbit_radius
        assert wp.orbit_until_target_altitude is not None
        self.orbit_until_target_altitude = wp.orbit_until_target_altitude
        assert wp.orbit_clockwise is not None
        self.orbit_clockwise = wp.orbit_clockwise


class RouteFollwingNavigator(AbstractNavigator):
    def __init__(self):
        self.route = list()

    def update_from_base(self, update: Route):
        assert isinstance(update, Route)
        for protowp in Route.routes:
            self.route.append()

    def update_from_flight_controller(self, update: DroneMessage):
        pass

    def get_command_update(self):
        pass
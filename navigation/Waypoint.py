from communicationProtocol_pb2 import Route, DroneMessage, Waypoint as ProtoWp

class Waypoint():
    def __init__(self):
        self.latitude = 0
        self.longitude = 0
        self.altitude = 0

        self.orbit_radius = 0
        self.orbit_until_target_altitude = False
        self.orbit_clockwise = False

    def set_latlon(self, lat, lon, alt, orbit_radius, orbit_until_target_altitude=False, orbit_clockwise=False):
        self.latitude = lat
        self.longitude = lon
        self.altitude = alt

        self.orbit_radius = orbit_radius
        self.orbit_until_target_altitude = orbit_until_target_altitude
        self.orbit_clockwise = orbit_clockwise

    def set_from_protoWP(self, wp: ProtoWp):
        self.latitude = wp.latitude
        self.longitude = wp.longitude
        self.altitude = wp.altitude

        assert wp.orbit_radius is not None
        self.orbit_radius = wp.orbit_radius
        assert wp.orbit_until_target_altitude is not None
        self.orbit_until_target_altitude = wp.orbit_until_target_altitude
        assert wp.orbit_clockwise is not None
        self.orbit_clockwise = wp.orbit_clockwise
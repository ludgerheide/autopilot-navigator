from communicationProtocol_pb2 import DroneMessage
import typing

class DecodedMessage:
    def __init__(self):
        self.timestamp = 0

        self.latitude = 0
        self.longitude = 0
        self.gps_altitude = 0
        self.baro_altitude = 0

        self.voltage = 0
        self.current = 0

    def __init__(self, encodedMessage: bytes):
        msg = DroneMessage()
        msg.ParseFromString(encodedMessage)

        assert msg.current_position is not None
        assert msg.current_battery_data is not None
        assert msg.current_altitude is not None
        assert msg.timestamp is not None

        self.timestamp = msg.timestamp / 1000000

        self.latitude = msg.current_position.latitude
        self.longitude = msg.current_position.longitude
        self.gps_altitude = msg.current_position.gps_altitude / 100
        self.baro_altitude = msg.current_altitude.altitude / 100

        self.voltage = msg.current_battery_data.voltage / 1000
        self.current = msg.current_battery_data.current / 1000

    def encode(self) -> bytes:
        msg = DroneMessage()

        msg.timestamp = round(self.timestamp * 1000000)

        msg.current_position.latitude = self.latitude
        msg.current_position.longitude = self.longitude
        msg.current_position.gps_altitude = round(self.gps_altitude * 100)

        msg.current_altitude.altitude = round(self.baro_altitude * 100)

        msg.current_battery_data.current = round(self.current * 1000)
        msg.current_battery_data.voltage = round(self.voltage * 1000)
        return msg.SerializeToString()

    def __str__(self):
        return "Pos: {},{} GpsAlt: {:.1f} m, BaroAlt {:.1f} m, Battery {:.1f} V {:.1f} A".format(self.latitude, self.longitude, self.gps_altitude, self.baro_altitude, self.voltage, self.current)
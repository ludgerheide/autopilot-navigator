import shlex
import signal
import subprocess
import sqlite3


class VideoRecorder():
    BITRATE = 4  # MBit/s
    _BITRATE_CMD = "v4l2-ctl -c video_bitrate={}".format(int(BITRATE * 1000000))

    WIDTH = 640
    HEIGHT = 480


    def __init__(self, udp_stream=False, dst_ip="255.255.255.255"):
        self._CMD_STREAM = "gst-launch-1.0 -e v4l2src do-timestamp=true ! video/x-h264,width={},height={},framerate=30/1 ! h264parse ! tee name=t ! queue ! mp4mux ! filesink location={}.mp4 t. ! queue ! rtph264pay ! udpsink host={} port=9000".format(
            WIDTH, HEIGHT)
        self._CMD_NOSTREAM = "gst-launch-1.0 -e v4l2src do-timestamp=true ! video/x-h264,width={},height={},framerate=30/1 ! h264parse ! mp4mux ! filesink location={}.mp4".format(
            WIDTH, HEIGHT)

        # Setup the Bitrate
        args = shlex.split(self._BITRATE_CMD)
        p = subprocess.Popen(args)
        p.wait()

        self._start_recording(udp_stream)

    def _get_filename(self):
        conn = sqlite3.connect('flightLogs.sqlite')
        c = conn.cursor()
        c.execute('SELECT MAX(Id) FROM flights;')
        flightId = c.fetchone()
        flightId = flightId[0]
        conn.close()

        filename = "video-{}".format(flightId)
        return filename

    def _start_recording(self, udp_stream, dst_ip):
        # Start the video recording
        if udp_stream:
            args = shlex.split(self._CMD_STREAM.format(self._get_filename(), dst_ip))
        else:
            args = shlex.split(self._CMD_NOSTREAM)
        self.process = subprocess.Popen(args)

    def restart(self, udp_stream=False):
        print("Video recorder restarting…")
        self.process.send_signal(signal.SIGINT)
        self.process.wait()

        self._start_recording(udp_stream)

    def quit(self):
        print("Video recorder exiting…")
        self.process.send_signal(signal.SIGINT)
        self.process.wait()

class SerialConnector():
    SERIALCONNECTOR_CMD = "./serialConnector"

    def __init__(self):
        # Setup the Bitrate
        args = shlex.split(self.SERIALCONNECTOR_CMD)
        self.process = subprocess.Popen(args)

    def reload(self):
        print("Video recorder reloading…")
        self.process.send_signal(signal.SIGINT)

    def quit(self):
        print("Serial connector exiting…")
        self.process.send_signal(signal.SIGINT)
        self.process.wait()
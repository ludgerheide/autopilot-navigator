import shlex
import signal
import subprocess
import sqlite3
import os
import time


class VideoRecorder():
    BITRATE = 4  # MBit/s
    _BITRATE_CMD = "v4l2-ctl -c video_bitrate={}".format(int(BITRATE * 1000000))

    WIDTH = 640
    HEIGHT = 480


    def __init__(self, udp_stream=False, dst_ip="255.255.255.255"):
        self.FIRST_CMD = "gst-launch-1.0 -e v4l2src do-timestamp=true ! video/x-h264,width={},height={},framerate=30/1 ! h264parse ".format(self.WIDTH, self.HEIGHT)
        self._CMD_STREAM = self.FIRST_CMD + "! tee name=t ! queue ! mp4mux ! filesink location={}.mp4 t. ! queue ! rtph264pay ! udpsink host={} port=9000"
        self._CMD_NOSTREAM = self.FIRST_CMD + "! mp4mux ! filesink location={}.mp4"

        # Setup the Bitrate
        args = shlex.split(self._BITRATE_CMD)
        p = subprocess.Popen(args)
        p.wait()

        self._start_recording(udp_stream, dst_ip)

    def _get_filename(self):
        if not (os.path.exists('flightLogs.sqlite') and os.path.exists('flightLogs.sqlite-shm') and os.path.exists('flightLogs.sqlite-wal')):
            # Sleep up to 5 seconds of the database isn't completely there yet
            for i in range(10):
                print("Database isn't ready, sleeping up to {} more seconds…".format(10-i))
                time.sleep(1)
        i = 0
        while i < 5:
            conn = sqlite3.connect('flightLogs.sqlite')
            try:
                c = conn.cursor()
                c.execute('SELECT MAX(Id) FROM flights;')
                flightId = c.fetchone()
                flightId = flightId[0]
                break
            except sqlite3.OperationalError as e:
                print("Error encountered, waiting")
                i += 1
                time.sleep(1)
            finally:
                conn.close()

        filename = "video-{}".format(flightId)
        return filename

    def _start_recording(self, udp_stream, dst_ip):
        # Start the video recording
        if udp_stream:
            args = shlex.split(self._CMD_STREAM.format(self._get_filename(), dst_ip))
        else:
            args = shlex.split(self._CMD_NOSTREAM.format(self._get_filename()))
        self.process = subprocess.Popen(args, start_new_session=True)

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
        self.process = subprocess.Popen(args, start_new_session=True)

    def reload(self):
        print("Serial connector reloading…")
        self.process.send_signal(signal.SIGHUP)

    def quit(self):
        print("Serial connector exiting…")
        self.process.send_signal(signal.SIGINT)
        self.process.wait()
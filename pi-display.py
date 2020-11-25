#!/usr/bin/python3
import digitalio
import busio
import board
import sys
import os
import psutil
import logging
import time
from adafruit_epd.epd import Adafruit_EPD
from adafruit_epd.ssd1675 import Adafruit_SSD1675
from telnetlib import Telnet

TELNET_EOM_BYTE_STR = b"---EOM---"
TELNET_EOM_STR = "---EOM---"


"""
TODO How to get Pi-hole info from both pi-holes? 
    - Expose telnet api on a lan-visible interface for pi-zero
        - Would need to forward port 4711 from localhost to something in 192.168.1.x
        - I think either eth0 or wlan0 would work
TODO How to get system info from both pi-holes?
    - Create telnet api and have a python program running on both machines. One asks for perf info
    via telnet, the other answers
        - Pi_3b is server, pi zero would be client
"""


def strip_eom(text):
    if text.endswith(TELNET_EOM_STR):
        return text[:-len(TELNET_EOM_STR)].strip()
    else:
        return text.strip()


def setup_logger():
    log = logging.getLogger('pi-display')
    log.setLevel(logging.DEBUG)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    log.addHandler(console_handler)
    return log


log = setup_logger()


class PiDisplayController:

    def __init__(self):
        # create the spi device and pins we will need
        self.spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)
        self.ecs = digitalio.DigitalInOut(board.CE0)
        self.dc = digitalio.DigitalInOut(board.D22)
        self.rst = digitalio.DigitalInOut(board.D27)
        self.busy = digitalio.DigitalInOut(board.D17)
        self.sramcs_pin = None

        self.eink = Adafruit_SSD1675(
            122, 250, self.spi,
            cs_pin=self.ecs, dc_pin=self.dc, sramcs_pin=self.sramcs_pin,
            rst_pin=self.rst, busy_pin=self.busy)
        log.info("Created display")
        self.eink.rotation = 3

        self.tn = Telnet('127.0.0.1', 4711)
        log.info("Opened telnet connection")

    def get_pihole_version(self, tn: Telnet):
        tn.write(b">version")
        log.info("Getting pihole version...")
        response = tn.read_until(TELNET_EOM_BYTE_STR).decode('ascii')
        return strip_eom(response)

    def get_pihole_stats(self, tn: Telnet):
        tn.write(b">stats")
        log.info("Getting pihole stats...")
        response = tn.read_until(TELNET_EOM_BYTE_STR).decode('ascii')
        return strip_eom(response)

    def draw_perf_stats(self):
        log.info("Clearing display buffer")
        self.eink.fill(Adafruit_EPD.WHITE)

        version_info = self.get_pihole_version(self.tn)
        stats = self.get_pihole_stats(self.tn)
        log.info("Pulled performance data off telnet")

        loadavg = os.getloadavg()
        log.info("Pulled performance data off os")

        cpu_usage = psutil.cpu_percent(interval=1, percpu=True)
        vmem = psutil.virtual_memory()
        root_disk_usage = psutil.disk_usage('/')
        temp_info = psutil.sensors_temperatures()
        boot_time = psutil.boot_time()
        log.info("Pulled performance data off os")

        SEPARATOR = "\n------------------\n"
        perf_info = (
            f"{SEPARATOR}"
            f"pi-hole version info:\n\n{version_info}"
            f"{SEPARATOR}"
            f"ad-blocking stats:\n\n{stats}"
            f"{SEPARATOR}"
            f"system load avg:{loadavg}"
            f"{SEPARATOR}"
            f"cpu usage:{cpu_usage}"
            f"{SEPARATOR}"
            f"temp (celsius):{temp_info}"
            f"{SEPARATOR}"
            f"memory:{vmem}"
            f"{SEPARATOR}"
            f"root disk usage:{root_disk_usage}"
            f"{SEPARATOR}"
            f"boot_time:{boot_time}"
            f"{SEPARATOR}")
        x = 1
        y = 1
        self.eink.text(perf_info, x, y, Adafruit_EPD.BLACK)
        log.info("Drawing eink buffer")
        self.eink.display()

    def __del__(self):
        self.tn.close()
        log.info("Closed telnet connection")

    def wait_for_display_interval(self):
        DISPLAY_WRITE_INTERVAL_SEC = 60 * 3
        log.info(
            f"Waiting for {DISPLAY_WRITE_INTERVAL_SEC} seconds before writing to display")
        time_waited_sec = 0
        while time_waited_sec < DISPLAY_WRITE_INTERVAL_SEC:
            time.sleep(30)
            time_waited_sec += 30
            log.info(
                f"{DISPLAY_WRITE_INTERVAL_SEC - time_waited_sec} seconds left to wait")


def main():
    log.info("--------------------------------"
             f"\n{sys.argv[0]}\n"
             "--------------------------------")
    disp = PiDisplayController()
    disp.draw_perf_stats()
    disp.wait_for_display_interval()


if __name__ == '__main__':
    main()

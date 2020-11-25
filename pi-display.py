#!/usr/bin/python3
import digitalio
import argparse
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
from logging import handlers

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
    LOG_NAME = 'pi-display.log'
    if os.path.exists(LOG_NAME):
        os.remove(LOG_NAME)

    base_logger = logging.getLogger()
    base_logger.setLevel(logging.DEBUG)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    base_logger.addHandler(console_handler)

    file_handler = handlers.TimedRotatingFileHandler(
        filename=LOG_NAME, when='D', interval=1, backupCount=3, encoding='utf-8', delay=False)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(
        "%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s"))
    base_logger.addHandler(file_handler)

    return base_logger


log = setup_logger()


class PiDisplayController:

    def __init__(self, drawing_enabled: bool):
        self.drawing_enabled = drawing_enabled

        if self.drawing_enabled:
            log.info("Drawing enabled, writing output to eink display")
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
        else:
            log.info("Drawing disabled, writing output to log instead")
            self.eink = None

        self.tn = Telnet('127.0.0.1', 4711)
        log.info("Opened telnet connection")

    def get_pihole_version(self, tn: Telnet):
        tn.write(b">version")
        log.info("Getting pihole version...")
        response = tn.read_until(TELNET_EOM_BYTE_STR).decode('ascii')
        log.info("Pulled version info off telnet")
        return strip_eom(response)

    def get_pihole_stats(self, tn: Telnet):
        tn.write(b">stats")
        log.info("Getting pihole stats...")
        response = tn.read_until(TELNET_EOM_BYTE_STR).decode('ascii')
        log.info("ad blocking stats off telnet")
        return strip_eom(response)

    def get_system_info(self):
        loadavg = os.getloadavg()
        log.info("Pulled performance data off os")
        cpu_usage = psutil.cpu_percent(interval=1, percpu=True)
        vmem = psutil.virtual_memory()
        root_disk_usage = psutil.disk_usage('/')
        temp_info = psutil.sensors_temperatures()
        boot_time = psutil.boot_time()
        log.info("Pulled performance data off psutil")
        return (
            f"system load avg:{loadavg}\n"
            f"cpu usage:{cpu_usage}\n"
            f"temp (celsius):{temp_info}\n"
            f"memory:{vmem}\n"
            f"root disk usage:{root_disk_usage}\n"
            f"boot_time:{boot_time}"
        )

    def update_display(self, text):
        if self.drawing_enabled:
            log.info("Clearing display buffer")
            self.eink.fill(Adafruit_EPD.WHITE)
            x = 1
            y = 1
            self.eink.text(text, x, y, Adafruit_EPD.BLACK)
            log.info("Drawing eink buffer")
            self.eink.display()
        else:
            log.info(f"Not drawn to display:")
            log.info(f"------------------------------")
            log.info(f"{text}")
            log.info(f"------------------------------")

        # Done even if drawing isn't enabled so the log isn't spammed
        self.wait_for_display_interval()

    def run(self):
        version_info = self.get_pihole_version(self.tn)
        # Page 1:
        self.update_display(f"pi-hole version info:\n{version_info}")

        blocking_stats = self.get_pihole_stats(self.tn)
        # Page 2:
        self.update_display(f"pi-hole ad-blocking stats:\n{blocking_stats}")

        system_info = self.get_system_info()
        # Page 3:
        self.update_display(f"System performance:\n{system_info}")

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
    log.info("--------------------------------")
    log.info(f"{sys.argv[0]}")
    log.info("--------------------------------")
    parser = argparse.ArgumentParser(
        description='Print pi-hole performance data')
    parser.add_argument('--no-draw', dest='drawing_disabled', action='store_true',
                        help='Print to log instead of display')
    args = parser.parse_args()
    disp = PiDisplayController(drawing_enabled=not args.drawing_disabled)
    disp.run()


if __name__ == '__main__':
    main()

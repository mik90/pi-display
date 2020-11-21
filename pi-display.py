#!/usr/bin/python3
import digitalio
import busio
import board
import sys
import os
import psutil
import logging
from adafruit_epd.epd import Adafruit_EPD
from adafruit_epd.ssd1675 import Adafruit_SSD1675
from telnetlib import Telnet

TELNET_EOM_BYTE_STR = b"---EOM---"
TELNET_EOM_STR = "---EOM---"


def setup_logger():
    log = logging.getLogger('pi-display')
    log.setLevel(logging.DEBUG)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    log.addHandler(console_handler)
    return log


log = setup_logger()


def strip_eom(text):
    if text.endswith(TELNET_EOM_STR):
        return text[:-len(TELNET_EOM_STR)].strip()
    else:
        return text.strip()


def get_pihole_version(tn: Telnet):
    tn.write(b">version")
    log.info("Getting pihole version...")
    response = tn.read_until(TELNET_EOM_BYTE_STR).decode('ascii')
    return strip_eom(response)


def get_pihole_stats(tn: Telnet):
    tn.write(b">stats")
    log.info("Getting pihole stats...")
    response = tn.read_until(TELNET_EOM_BYTE_STR).decode('ascii')
    return strip_eom(response)


"""
TODO How to get Pi-hole info from both pi-holes? 
      - Expose telnet api on a lan-visible interface for pi-zero
          - Would need to forward port 4711 from localhost to something in 192.168.1.x
          - I think either eth0 or wlan0 would work
TODO How to get system info from both pi-holes?
    - Create telnet api and have a python program running on both machines
        - Pi_3b is server, pi zero would be client
"""


def setup_display():
    # create the spi device and pins we will need
    spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)
    ecs = digitalio.DigitalInOut(board.D12)
    dc = digitalio.DigitalInOut(board.D11)

    srcs = digitalio.DigitalInOut(board.D10)
    rst = digitalio.DigitalInOut(board.D9)
    busy = digitalio.DigitalInOut(board.D5)

    log.info("Creating display")
    display = Adafruit_SSD1675(
        122, 250, spi,
        cs_pin=ecs, dc_pin=dc, sramcs_pin=srcs,
        rst_pin=rst, busy_pin=busy)

    display.rotation = 1

    # clear the buffer
    log.info("Clear buffer")
    display.fill(Adafruit_EPD.WHITE)
    display.pixel(10, 100, Adafruit_EPD.BLACK)

    log.info("Draw text")
    display.text('hello world', 25, 10, Adafruit_EPD.BLACK)
    display.display()


def main():
    log.info("--------------------------------"
             f"\n{sys.argv[0]}\n"
             "--------------------------------")
    with Telnet('127.0.0.1', 4711) as tn:
        version_info = get_pihole_version(tn)
        stats = get_pihole_stats(tn)
        cpu_usage = psutil.cpu_percent(interval=1, percpu=True)
        loadavg = os.getloadavg()
        vmem = psutil.virtual_memory()
        root_disk_usage = psutil.disk_usage('/')
        temp_info = psutil.sensors_temperatures()
        boot_time = psutil.boot_time()
        log.info("Closing telnet connection\n")

    SEPARATOR = "\n------------------\n"
    log.info(
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
        f"{SEPARATOR}"
    )


if __name__ == '__main__':
    main()

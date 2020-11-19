#!/usr/bin/python3
import digitalio
import busio
import board
import sys
from adafruit_epd.epd import Adafruit_EPD
from adafruit_epd.ssd1675 import Adafruit_SSD1675
from telnetlib import Telnet


def get_pihole_version():
    with Telnet('127.0.0.1', 4711) as tn:
        tn.write(b">version")
        print("wrote \">version\"")
        response = tn.read_until(b"---EOM---")
        print(f"Version response={response.decode('ascii')}")

# TODO Get loadavg

# TODO Get memory usage

# TODO Get temperature

def setup_display():
    # create the spi device and pins we will need
    spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)
    ecs = digitalio.DigitalInOut(board.D12)
    dc = digitalio.DigitalInOut(board.D11)
    # can be None to use internal memory
    srcs = digitalio.DigitalInOut(board.D10)
    rst = digitalio.DigitalInOut(board.D9)    # can be None to not use this pin
    busy = digitalio.DigitalInOut(board.D5)   # can be None to not use this pin

    # give them all to our driver
    print("Creating display")
    display = Adafruit_SSD1675(
        122, 250, spi,
        cs_pin=ecs, dc_pin=dc, sramcs_pin=srcs,
        rst_pin=rst, busy_pin=busy)

    display.rotation = 1

    # clear the buffer
    print("Clear buffer")
    display.fill(Adafruit_EPD.WHITE)
    display.pixel(10, 100, Adafruit_EPD.BLACK)

    print("Draw text")
    display.text('hello world', 25, 10, Adafruit_EPD.BLACK)
    display.display()


def main():
    print("--------------------------------"
          f"\n{sys.argv[0]}\n"
          "--------------------------------")
    get_pihole_version()


if __name__ == '__main__':
    main()

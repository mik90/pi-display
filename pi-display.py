#!/usr/bin/python
import digitalio
import busio
import board
from adafruit_epd.epd import Adafruit_EPD
from adafruit_epd.il0373 import Adafruit_IL0373

"""
* Create weather/pihole/twitter-analyzer eInk UI
  - Guide is [here](https://github.com/adafruit/Adafruit_CircuitPython_EPD)
  - Product page is [here]((https://www.adafruit.com/product/4687)
  - Needs 8 wires:
    - SCK (SPI)
    - MOSI (SPI)
    - MISO (SPI)
    - D12
    - D11
    - D10 (opt)
    - D9 (opt)
    - D5 (opt)
  - This can be wired to the pi-hole without sitting directly on
    the board as a hat (or bonnet, as the brits say)
  - Display pi hole load avg, block percentage, and other stats
  - API can be done via shell or telnet
    - can use Python's telnetlib
"""


def main():
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
    # TODO Use the monochrome 2.13 inch display
    display = Adafruit_IL0373(104, 212, spi,          # 2.13" Tri-color display
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


if __name__ == '__main__':
    main()

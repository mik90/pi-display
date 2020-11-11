# pi-display
Reads pi-hole status and prints it out to eInk display  
Run this on the same board as the pi-hole so that the load data is available
This can be wired to the pi-hole without sitting directly on the board as a  
hat (or bonnet, as the brits say)  
Display pi hole load avg, block percentage, and other stats
Needs 8 wires:
- SCK (SPI)
- MOSI (SPI)
- MISO (SPI)
- D12
- D11
- D10 (optional)
- D9 (optional)
- D5 (optional)

### Display
- Product page [here](https://www.adafruit.com/product/4687)
- Weatherstation example [here](https://learn.adafruit.com/raspberry-pi-e-ink-weather-station-using-python/weather-station-code)
- CircuitPython API [here](https://github.com/adafruit/Adafruit_CircuitPython_EPD)

### Pihole API
- Telnet API [here](https://docs.pi-hole.net/ftldns/telnet-api/)
    - Can use telnetlib for this
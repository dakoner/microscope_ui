from micropython_dotstar import DotStar
from machine import SPI, Pin
import time

spi = SPI(sck=Pin(12), mosi=Pin(13), miso=Pin(18)) # Configure SPI - see note below
dotstar = DotStar(spi, 64, brightness=1) # Just one DotStar

pattern = [
    [1, 1, 1, 1, 1, 1, 1, 1],
    [1, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 1],
    [1, 1, 1, 1, 1, 1, 1, 1],
]
for i in range(8):
    for j in range(8):
        x = i*8 + j
        if pattern[i][j] == 1:
            dotstar[x] = (255, 255, 255)
        else:
            dotstar[x] = (0, 0, 0)

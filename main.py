# Example using PIO to drive a set of WS2812 LEDs.

#from ws2812 import pixels_fill, pixels_show, color_chase, rainbow_cycle
import ws2812
import time
import uasyncio

BLACK = (0, 0, 0)
RED = (255, 0, 0)
YELLOW = (255, 150, 0)
GREEN = (0, 255, 0)
CYAN = (0, 255, 255)
BLUE = (0, 0, 255)
PURPLE = (180, 0, 255)
WHITE = (255, 255, 255)
COLORS = (BLACK, RED, YELLOW, GREEN, CYAN, BLUE, PURPLE, WHITE)

async def main():
    print("fills")
    for color in COLORS:       
        ws2812.pixels_fill(color)
        ws2812.pixels_show()
        time.sleep(0.2)

    print("chases")
    for color in COLORS:       
        ws2812.color_chase(color, 0.01)

    print("rainbow")
    ws2812.rainbow_cycle(0)

if __name__ == "__main__":
    uasyncio.run(main())
    
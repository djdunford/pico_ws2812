# Example using PIO to drive a set of WS2812 LEDs.

import ws2812
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


async def rgb_test():
    try:
        print("rgb")
        ws2812.pixels_fill(BLACK)
        ws2812.pixels_set(2, RED)
        ws2812.pixels_set(4, GREEN)
        ws2812.pixels_set(7, BLUE)
        await ws2812.pixels_show()
    except uasyncio.CancelledError:
        pass


async def main():
    running_task = uasyncio.create_task(rgb_test())
    await running_task


if __name__ == "__main__":
    uasyncio.run(main())

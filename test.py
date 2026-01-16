# Example using PIO to drive a set of WS2812 LEDs.

import ws2812
import uasyncio
import utime

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
        while True:
            print("rgb")
        
            sleeptime = 0.75
        
            ws2812.pixels_fill(RED)
            await ws2812.pixels_show()
            await uasyncio.sleep(sleeptime)
            
            ws2812.pixels_fill(GREEN)
            await ws2812.pixels_show()
            await uasyncio.sleep(sleeptime)
            
            ws2812.pixels_fill(BLUE)
            await ws2812.pixels_show()
            await uasyncio.sleep(sleeptime)
            
    except uasyncio.CancelledError:
        pass
    
    
async def black():
    try:
        
        ws2812.pixels_fill((40,0,0))
        await ws2812.pixels_show()
        await uasyncio.sleep(0.01)
        
    except uasyncio.CancelledError:
        pass


async def main():
    running_task = uasyncio.create_task(black())
    await running_task


if __name__ == "__main__":
    uasyncio.run(main())

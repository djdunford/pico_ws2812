# Example using PIO to drive a set of WS2812 LEDs.

import ws2812
import uasyncio
import machine
import time

BLACK = (0, 0, 0)
RED = (255, 0, 0)
YELLOW = (255, 150, 0)
GREEN = (0, 255, 0)
CYAN = (0, 255, 255)
BLUE = (0, 0, 255)
PURPLE = (180, 0, 255)
WHITE = (255, 255, 255)
COLORS = (BLACK, RED, YELLOW, GREEN, CYAN, BLUE, PURPLE, WHITE)

button1 = machine.Pin(21, machine.Pin.IN, machine.Pin.PULL_UP)
button4 = machine.Pin(18, machine.Pin.IN, machine.Pin.PULL_UP)

debounce = 1


async def demo1():
    try:
        print("fills")
        for color in COLORS:
            ws2812.pixels_fill(color)
            await ws2812.pixels_show()
            await uasyncio.sleep(0.2)

        print("chases")
        for color in COLORS:
            await ws2812.color_chase(color, 0.01)

        print("rainbow")
        await ws2812.rainbow_cycle(0)
    except uasyncio.CancelledError:
        pass

async def blank():
    try:
        print("blanking")
        ws2812.pixels_fill(BLACK)
        await ws2812.pixels_show()
    except uasyncio.CancelledError:
        pass


async def main():
    pressed = time.time()-debounce
    running_task = None
    while True:
        if not button1.value() and time.time() > pressed+debounce:
            print("button 1")
            pressed=time.time()
            if running_task:
                print("cancelling existing")
                running_task.cancel()
                await running_task
                print("cancelled existing")
            running_task = uasyncio.create_task(blank())
        if not button4.value() and time.time() > pressed+debounce:
            print("button 4")
            pressed=time.time()
            if running_task:
                print("cancelling existing")
                running_task.cancel()
                await running_task
                print("cancelled existing")
            running_task = uasyncio.create_task(demo1())
        await uasyncio.sleep(0.05)

if __name__ == "__main__":
    uasyncio.run(main())

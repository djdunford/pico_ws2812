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
button2 = machine.Pin(20, machine.Pin.IN, machine.Pin.PULL_UP)
button3 = machine.Pin(19, machine.Pin.IN, machine.Pin.PULL_UP)
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


async def blue_green():
    try:
        print("blue green")
        for i in range(100):
            if (i % 3) == 0:
                ws2812.pixels_set(i, BLUE)
            elif (i % 3) == 1:
                ws2812.pixels_set(i, GREEN)
            else:
                ws2812.pixels_set(i, CYAN)
        await ws2812.pixels_show()
    except uasyncio.CancelledError:
        pass


async def rgb():
    try:
        print("rgb")
        for i in range(100):
            if (i % 3) == 0:
                ws2812.pixels_set(i, RED)
            elif (i % 3) == 1:
                ws2812.pixels_set(i, GREEN)
            else:
                ws2812.pixels_set(i, BLUE)
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
        if not button3.value() and time.time() > pressed+debounce:
            print("button 3")
            pressed=time.time()
            if running_task:
                print("cancelling existing")
                running_task.cancel()
                await running_task
                print("cancelled existing")
            running_task = uasyncio.create_task(blue_green())
        if not button2.value() and time.time() > pressed+debounce:
            print("button 2")
            pressed=time.time()
            if running_task:
                print("cancelling existing")
                running_task.cancel()
                await running_task
                print("cancelled existing")
            running_task = uasyncio.create_task(rgb())
        await uasyncio.sleep(0.05)


if __name__ == "__main__":
    uasyncio.run(main())

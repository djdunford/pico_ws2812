# Example using PIO to drive a set of WS2812 LEDs.

import ws2812
import uasyncio
import machine
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

button1 = machine.Pin(21, machine.Pin.IN, machine.Pin.PULL_UP)
button2 = machine.Pin(20, machine.Pin.IN, machine.Pin.PULL_UP)
button3 = machine.Pin(19, machine.Pin.IN, machine.Pin.PULL_UP)
button4 = machine.Pin(18, machine.Pin.IN, machine.Pin.PULL_UP)

print("Starting")
led = machine.Pin(17, machine.Pin.OUT)

debounce = 1

machine.freq(180000000)


async def blank():
    try:
        print("blanking")
        ws2812.pixels_fill(BLACK)
        await ws2812.pixels_show()
    except uasyncio.CancelledError:
        pass


async def blue_green(milli_brightness:int=1000):
    try:
        print(f"blue green cycle: brightness {milli_brightness}")
        color_range = list(range(85, 170, 1)) + list(range(169, 86, -1))
        await ws2812.rainbow_cycle_2(0, color_range, 2592000, 100, 1.5, milli_brightness)
        print(f"blue green cycle ended: brightness {milli_brightness}")
    except uasyncio.CancelledError:
        pass


async def enchanted_forest_base():
    try:
        print("enchanted forest base")
        await ws2812.enchanted_forest_base()
        print("enchanted forest base ended")
    except uasyncio.CancelledError:
        pass


async def led_flash():
    try:
        start_time = utime.time()
        while True:
            while utime.time() < start_time + 1:
                await uasyncio.sleep(0.05)
            led.value(1)
            await uasyncio.sleep(0.02)
            led.value(0)
            start_time += 3
    except uasyncio.CancelledError:
        pass


async def main():
    pressed = utime.time()-debounce
    running_task = None
    uasyncio.create_task(led_flash())
    print("flasher running")
    while True:
        if not button1.value() and utime.time() > pressed+debounce:
            print("button 1")
            pressed=utime.time()
            if running_task:
                print("cancelling existing")
                running_task.cancel()
                await running_task
                print("cancelled existing")
            running_task = uasyncio.create_task(blank())
        if not button4.value() and utime.time() > pressed+debounce:
            print("button 4")
            pressed=utime.time()
            if running_task:
                print("cancelling existing")
                running_task.cancel()
                await running_task
                print("cancelled existing")
            running_task = uasyncio.create_task(enchanted_forest_base())
        if not button3.value() and utime.time() > pressed+debounce:
            print("button 3")
            pressed=utime.time()
            if running_task:
                print("cancelling existing")
                running_task.cancel()
                await running_task
                print("cancelled existing")
            running_task = uasyncio.create_task(blue_green())
        if not button2.value() and utime.time() > pressed+debounce:
            print("button 2")
            pressed=utime.time()
            if running_task:
                print("cancelling existing")
                running_task.cancel()
                await running_task
                print("cancelled existing")
            running_task = uasyncio.create_task(blue_green(200))
        await uasyncio.sleep(0.05)


if __name__ == "__main__":
    uasyncio.run(main())

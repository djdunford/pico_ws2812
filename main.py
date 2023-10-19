# Example using PIO to drive a set of WS2812 LEDs.

import ws2812
import time
import uasyncio
import machine

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

running_task = None


async def demo1():
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


async def blank():
    print("blanking")
    ws2812.pixels_fill(BLACK)
    ws2812.pixels_show()


def launch(pin):
    print("button pressed")
    global running_task
    if running_task:
        print("cancelling")
        running_task.cancel()
        running_task = None
    if pin is button1:
        print("button 1")
        running_task = uasyncio.run(demo1())
    if pin is button4:
        print("button 4")
        running_task = uasyncio.run(blank())


async def main():
    button1.irq(trigger=machine.Pin.IRQ_FALLING, handler=launch)
    button4.irq(trigger=machine.Pin.IRQ_FALLING, handler=launch)


if __name__ == "__main__":
    uasyncio.run(main())

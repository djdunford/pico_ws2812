# Example using PIO to drive a set of WS2812 LEDs.

import ws2812
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
button_pressed = None


async def demo1():
    print("fills")
    for color in COLORS:       
        ws2812.pixels_fill(color)
        await ws2812.pixels_show()
        uasyncio.sleep(0.2)

    print("chases")
    for color in COLORS:       
        await ws2812.color_chase(color, 0.01)

    print("rainbow")
    await ws2812.rainbow_cycle(0)


async def blank():
    print("blanking")
    ws2812.pixels_fill(BLACK)
    ws2812.pixels_show()


def launch(pin):
    global button_pressed
    print("button pressed")
    button_pressed = pin


async def main():
    global button_pressed
    global running_task
    button1.irq(trigger=machine.Pin.IRQ_FALLING, handler=launch)
    button4.irq(trigger=machine.Pin.IRQ_FALLING, handler=launch)
    while True:
        if button_pressed is button1:
            print("button 1")
            button_pressed = None
            if running_task:
                print("cancelling existing")
                running_task.cancel()
            running_task = uasyncio.create_task(blank())
        if button_pressed is button4:
            print("button 4")
            button_pressed = None
            if running_task:
                print("cancelling existing")
                running_task.cancel()
            running_task = uasyncio.create_task(demo1())
        await uasyncio.sleep(0.05)

if __name__ == "__main__":
    uasyncio.run(main())

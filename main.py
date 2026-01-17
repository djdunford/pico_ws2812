# Example using PIO to drive a set of WS2812 LEDs.

import ws2812
import uasyncio
import machine
import utime
import LCD1602
import random
import math
from micropython import const

machine.freq(180000000)

# mock class should the LCD not be detected
class NoLcd:
    def print_lcd(self, _m):
        return
    def setCursor(self, _x, _y):
        return
    def printout(self, _m):
        return

try:
    lcd = LCD1602.LCD1602(16,2)
except OSError:
    lcd = NoLcd()

BLACK = (0, 0, 0)

LED_PIN = const(17)
LED_DUTY_CYCLE = const(5000)  # PWM rate, out of 65535
LED_FREQUENCY = const(5000)  # PWM frequency, in Hz

buttons = []
buttons.append(machine.Pin(21, machine.Pin.IN, machine.Pin.PULL_UP))
buttons.append(machine.Pin(20, machine.Pin.IN, machine.Pin.PULL_UP))
buttons.append(machine.Pin(19, machine.Pin.IN, machine.Pin.PULL_UP))
buttons.append(machine.Pin(18, machine.Pin.IN, machine.Pin.PULL_UP))

print("Starting")
led = machine.PWM(machine.Pin(LED_PIN, machine.Pin.OUT))
led.freq(LED_FREQUENCY)

debounce_ms = const(1000)

async def blank():
    try:
        lcd.print_lcd("ALL OFF")
        print("blanking")
        ws2812.pixels_fill(BLACK)
        await ws2812.pixels_show()
    except uasyncio.CancelledError:
        pass
    
    
loopstarts = [ 0,21,39,55,71, 90,106,125,142,158,175,192,210,229,249,265]
loopends =   [20,38,54,70,89,105,124,140,157,174,191,209,228,248,264,283]

def scale_colour(rgb,factor):
    return tuple(math.ceil(c // factor) for c in rgb)

def dim_colour(rgb,brightness):
    return tuple(math.ceil(c * max(min(brightness,100),0) // 100) for c in rgb)

scalenum = 16

BLACK = (0,0,0)
RED = scale_colour((255, 0, 0),scalenum) 
YELLOW = scale_colour((255, 150, 0),scalenum)
GREEN = scale_colour((0, 255, 0),scalenum)
CYAN = scale_colour((0, 255, 255),scalenum)
BLUE = scale_colour((0, 0, 255),scalenum)
PURPLE = scale_colour((180, 0, 255),scalenum)
WHITE = scale_colour((255, 255, 255),scalenum)

COLORS = (BLACK, RED, YELLOW, GREEN, CYAN, BLUE, PURPLE, WHITE)


def loop_filler(loopnum,colournum,brightness):
    try:
        
        for i in range(loopstarts[loopnum],loopends[loopnum]):
            
            ws2812.pixels_set(i, dim_colour(colournum,brightness))
            
    except uasyncio.CancelledError:
        pass

    
async def colour_loop():
    try:
        lcd.print_lcd("PARTY LIGHTS")

        segment_colours = [0] * len(loopstarts)
        last_step = -1
        start_time = utime.ticks_ms()
        fade_out = False
        fade_start_time = start_time

        while not fade_out or utime.ticks_diff(utime.ticks_ms(), fade_start_time) < 1000:
            elapsed = utime.ticks_diff(utime.ticks_ms(), start_time)
            step = elapsed // 850

            if step != last_step:
                last_step = step
                for j in range(len(loopstarts)):
                    while True:
                        randnum = random.randint(0,100) % 7 + 1
                        if randnum != segment_colours[j]:
                            segment_colours[j] = randnum
                            break

            for j in range(len(loopstarts)):
                if fade_out:
                    fade_elapsed = utime.ticks_diff(utime.ticks_ms(), fade_start_time)
                    brightness = max(100 - (fade_elapsed // 10), 0)
                    loop_filler(j, COLORS[segment_colours[j]], brightness)
                else:
                    brightness = min(elapsed // 10, 100)
                    loop_filler(j, COLORS[segment_colours[j]], brightness)
                
            await ws2812.pixels_show()
            
            if not fade_out and next_button_pressed.is_set():
                next_button_pressed.clear()
                print("fading out")
                lcd.print_lcd("PARTY FADEOUT")
                fade_out = True
                fade_start_time = utime.ticks_ms()

        ws2812.pixels_fill(BLACK)
        await ws2812.pixels_show()
        print("all off")
        lcd.print_lcd("ALL OFF")
        
    except uasyncio.CancelledError:
        pass
    
    
async def starlight():
    try:
        print("starlight")
        
        await ws2812.starlight(lcd, next_button_pressed)
        print("starlight ended")
    except uasyncio.CancelledError:
        pass


async def led_flash():
    try:
        print("flasher running")
        start_time = utime.time()
        while True:
            while utime.time() < start_time + 1:
                await uasyncio.sleep(0.05)
            led.duty_u16(LED_DUTY_CYCLE)
            await uasyncio.sleep(0.02)
            led.duty_u16(0)
            start_time += 3
    except uasyncio.CancelledError:
        pass

next_button_pressed = uasyncio.Event()

async def main():
    lcd.print_lcd("Starting")
    print("Starting loop")
    pressed = utime.ticks_ms()
    running_task = uasyncio.create_task(blank())
    uasyncio.create_task(led_flash())
    while True:

        # Blank all lights
        if not buttons[0].value() and utime.ticks_diff(utime.ticks_ms(), pressed) > debounce_ms:
            print("button 1")
            pressed=utime.ticks_ms()
            if running_task:
                print("cancelling existing")
                running_task.cancel()
                await running_task
                print("cancelled existing")
            next_button_pressed.clear()
            running_task = uasyncio.create_task(blank())

        # Change colour
        if not buttons[1].value() and utime.ticks_diff(utime.ticks_ms(), pressed) > debounce_ms:
            print("button 4 - party colours")
            pressed=utime.ticks_ms()
            if running_task:
                print("cancelling existing")
                running_task.cancel()
                await running_task
                print("cancelled existing")
            next_button_pressed.clear()
            running_task = uasyncio.create_task(colour_loop())

        # set Next event trigger
        if not buttons[3].value() and utime.ticks_diff(utime.ticks_ms(), pressed) > debounce_ms:
            print("next button pressed")
            pressed=utime.ticks_ms()
            next_button_pressed.set()

        # Start sequence
        if not buttons[2].value() and utime.ticks_diff(utime.ticks_ms(), pressed) > debounce_ms:
            print("button 3")
            pressed=utime.ticks_ms()
            if running_task:
                print("cancelling existing")
                running_task.cancel()
                await running_task
                print("cancelled existing")
            next_button_pressed.clear()
            running_task = uasyncio.create_task(starlight())

        await uasyncio.sleep(0)


if __name__ == "__main__":
    try:
        uasyncio.run(main())
    except KeyboardInterrupt:
        uasyncio.run(blank())
        print("clearing screen")
        lcd.print_lcd("")
        utime.sleep(3)
        print("exiting")

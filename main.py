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
    
scalenum = 6

def scale_colour(rgb,factor):
    return tuple(math.ceil(c / factor) for c in rgb)

BLACK = (0,0,0)
RED = scale_colour((255, 0, 0),scalenum) 
YELLOW = scale_colour((255, 150, 0),scalenum)
GREEN = scale_colour((0, 255, 0),scalenum)
CYAN = scale_colour((0, 255, 255),scalenum)
BLUE = scale_colour((0, 0, 255),scalenum)
PURPLE = scale_colour((180, 0, 255),scalenum)
WHITE = scale_colour((255, 255, 255),scalenum)
    
loopstarts = [ 0,21,39,55,71, 90,106,125,142,158,175,192,210,229,249,265]
loopends =   [20,38,54,70,89,105,124,140,157,174,191,209,228,248,264,283]

cads = [
    {"colour": RED, "lights": [2,3,4,5,6,7,8,9,10,11,12,13]},
    {"colour": GREEN, "lights": [18,19,20,21,22,23,25,26,27,28,29,30,31,32,33,34]},
    {"colour": BLUE, "lights": [36,37,38,39,40,41,42,43,44,45,46,47,48,49,50]},
    {"colour": PURPLE, "lights": [54,55,56,57,58,59,60,61,62,63,64,65,66,67]},
]


COLORS = (BLACK, RED, YELLOW, GREEN, CYAN, BLUE, PURPLE, WHITE)
    
async def loop_filler(loopnum,colournum):
    try:
        
        
        print(f"set loop {loopnum} to colour: {colournum}")
        
        for i in range(loopstarts[loopnum],loopends[loopnum]):
            
            ws2812.pixels_set(i, colournum)
            
    except uasyncio.CancelledError:
        pass
    
async def colour_loop():
    
    randnum = random.randint(0,100) % 7 + 1
    prevrandnum = 0
    
    try:
        lcd.print_lcd("PARTY LIGHTS")
        
        #fade in here?
        
        while True:
            for j in range(len(loopstarts)):
                
                while randnum  == prevrandnum:
                    randnum = random.randint(0,100) % 7 + 1
                
                await loop_filler(j, COLORS[randnum])
                
                prevrandnum = randnum
                
            prevrandnum = 0
            
            await ws2812.pixels_show()
            print("Colours shown")
            await uasyncio.sleep(0.85)
            
        # fade out here?
            
        lcd.print_lcd("ALL OFF")
        
    except uasyncio.CancelledError:
        pass


async def letters():
    try:
        print("letters")

        ws2812.pixels_fill(BLACK)
        
        while True:
            for letter in cads:
                for lednum in letter["lights"]:
                    ws2812.pixels_set(lednum, letter["colour"])
            await ws2812.pixels_show()
            await uasyncio.sleep(0.85)
            prevrandnum = 0
            for letter in cads:
                randnum = random.randint(0,100) % 7 + 1
                while randnum == prevrandnum:
                    randnum = random.randint(0,100) % 7 + 1
                prevrandnum = randnum
                letter["colour"] = COLORS[randnum]

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
    running_task = uasyncio.create_task(letters())
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
            print("button 4 - CADS letters")
            pressed=utime.ticks_ms()
            if running_task:
                print("cancelling existing")
                running_task.cancel()
                await running_task
                print("cancelled existing")
            next_button_pressed.clear()
            running_task = uasyncio.create_task(letters())

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

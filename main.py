# Example using PIO to drive a set of WS2812 LEDs.

import ws2812
import uasyncio
import machine
import utime
import LCD1602
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
            print("button 4 - switch colour")
            pressed=utime.ticks_ms()
            ws2812.TWINKLE_COLOUR = (ws2812.TWINKLE_COLOUR + 1) % len(ws2812.TWINKLE_COLOURS_RED)

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

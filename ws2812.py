import array
from machine import Pin
import rp2
import uasyncio
import utime
import random

# Configure the number of WS2812 LEDs.
NUM_LEDS = 400
PIN_NUM = 22


@rp2.asm_pio(sideset_init=rp2.PIO.OUT_LOW, out_shiftdir=rp2.PIO.SHIFT_LEFT, autopull=True, pull_thresh=24)
def ws2812():
    T1 = 2
    T2 = 5
    T3 = 3
    wrap_target()
    label("bitloop")
    out(x, 1)               .side(0)    [T3 - 1]
    jmp(not_x, "do_zero")   .side(1)    [T1 - 1]
    jmp("bitloop")          .side(1)    [T2 - 1]
    label("do_zero")
    nop()                   .side(0)    [T2 - 1]
    wrap()


# Create the StateMachine with the ws2812 program, outputting on pin
sm = rp2.StateMachine(0, ws2812, freq=8_000_000, sideset_base=Pin(PIN_NUM))

# Start the StateMachine, it will wait for data on its FIFO.
sm.active(1)

# Display a pattern on the LEDs via an array of LED RGB values.
ar = array.array("I", [0 for _ in range(NUM_LEDS)])


@micropython.native
async def pixels_show():
    dimmer_ar = array.array("I", [0 for _ in range(NUM_LEDS)])
    for i,c in enumerate(ar):
        r = (c >> 8) & 0xFF
        g = (c >> 16) & 0xFF
        b = c & 0xFF
        dimmer_ar[i] = (g<<16) + (r<<8) + b
    sm.put(dimmer_ar, 8)
    await uasyncio.sleep_ms(10)


def pixels_set(i, color):
    ar[i] = (color[0]<<16) + (color[1]<<8) + color[2]


@micropython.native
def pixels_fill(color):
    for i in range(len(ar)):
        pixels_set(i, color)


@micropython.native
def wheel(pos, milli_brightness:int=1000):
    # Input a value 0 to 255 to get a color value.
    # The colours are a transition r - g - b - back to r.
    if pos < 0 or pos > 255:
        return (0, 0, 0)
    if pos < 85:
        rising = pos * 3 * milli_brightness // 1000
        falling = (255 - pos * 3) * milli_brightness // 1000
        return (falling, rising, 0)
    if pos < 170:
        pos -= 85
        rising = pos * 3 * milli_brightness // 1000
        falling = (255 - pos * 3) * milli_brightness // 1000
        return (0, falling, rising)
    pos -= 170
    rising = pos * 3 * milli_brightness // 1000
    falling = (255 - pos * 3) * milli_brightness // 1000
    return (rising, 0, falling)
 
 
@micropython.native
async def rainbow_cycle_2(wait, color_range=list(range(255)), duration=10, speed=1, wavelength=1.0, milli_brightness=1000):
    start_time = utime.time()
    start_ticks = utime.ticks_ms()
    while utime.time() < start_time + duration:
        hue_offset = int(utime.ticks_diff(start_ticks, utime.ticks_ms()) * speed / 1000)
        for i in range(NUM_LEDS):
            arr_offset = (int(hue_offset + (i * wavelength))) % len(color_range)
            pixels_set(i, wheel(color_range[arr_offset], milli_brightness))
        await pixels_show()
        await uasyncio.sleep(wait)

@micropython.native
async def enchanted_forest_base():

    pause_fixed_ms = 150
    pause_max_variable_ms = 50
    twinkle_duration_ms = 400
    base_green_component = 100

    ticks = utime.ticks_ms()
    pause = random.randrange(pause_max_variable_ms)
    twinkles = []
    while True:
        pixels_fill((0,base_green_component,0))
        dice = random.randrange(50)
        while True:
            existing_twinkles = filter(lambda item: item["position"] == dice, twinkles)
            if all(False for _ in existing_twinkles):
                break
            dice = random.randrange(50)

        if utime.ticks_diff(utime.ticks_ms(), ticks) > pause_fixed_ms + pause:
            twinkles.append({
                "starttime": utime.ticks_ms(),
                "position": dice,
            })
            ticks = utime.ticks_ms()
            pause = random.randrange(pause_max_variable_ms)
        for twinkle in twinkles:
            offset = utime.ticks_diff(utime.ticks_ms(),twinkle["starttime"])
            red_blue_component = 255 - abs(((offset-twinkle_duration_ms) * 255) // twinkle_duration_ms)
            green_component = 255 - abs(((offset-twinkle_duration_ms) * (255-base_green_component)) // twinkle_duration_ms)
            pixels_set(twinkle["position"], (max(red_blue_component,0),max(green_component,base_green_component),max(red_blue_component,0)))
        if len(twinkles) > 0:
            if utime.ticks_diff(utime.ticks_ms(),twinkles[0]["starttime"]) > twinkle_duration_ms * 2:
                twinkles.pop(0)
        await pixels_show()
        await uasyncio.sleep(0)

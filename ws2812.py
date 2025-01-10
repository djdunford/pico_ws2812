import array
from machine import Pin
from micropython import const
import rp2
import uasyncio
import utime
import random
import gc

# Configure the number of WS2812 LEDs.
NUM_LEDS = const(300)  # must be a multiple of GROUP_SIZE
GROUP_SIZE = const(30)
PIN_NUM = const(22)


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


def pixels_fill(color):
    for i in range(len(ar)):
        pixels_set(i, color)


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


brightnesses = array.array("I", [30, 100, 200, 255, 200, 100])
brightness = array.array("I", [0 for _ in range(NUM_LEDS)])
for led in range(NUM_LEDS):
    brightness[led] = brightnesses[led % 6]


async def fast_sequence(next_button_pressed, twinkles, ticks):
    period_ms = 900
    twinkle_duration_ms = 300
    red = 0
    green = 255
    blue = 0

    next_led = 5

    while not next_button_pressed.is_set():
        for led in range(NUM_LEDS):
            pixels_set(led, (
                (red*brightness[led]) // 255,
                (green*brightness[led]) // 255,
                (blue*brightness[led]) // 255
            ))

        if utime.ticks_diff(utime.ticks_ms(), ticks) >= period_ms:
            for i in range(0, NUM_LEDS, GROUP_SIZE):
                twinkles.append({
                    "starttime": utime.ticks_ms(),
                    "position": next_led + i,
                })
                twinkles.append({
                    "starttime": utime.ticks_ms(),
                    "position": next_led + i + 2,
                })
            ticks = utime.ticks_ms()
            next_led = (next_led + 10) % GROUP_SIZE

        for twinkle in twinkles:
            offset = utime.ticks_diff(utime.ticks_ms(),twinkle["starttime"])
            red_blue_component = 255 - abs(((offset-twinkle_duration_ms) * 255) // twinkle_duration_ms)
            green_component = 255 - abs(((offset-twinkle_duration_ms) * (255-brightness[twinkle["position"]])) // twinkle_duration_ms)
            pixels_set(twinkle["position"], (max(red_blue_component,0),max(green_component,brightness[twinkle["position"]]),max(red_blue_component,0)))
        
        while (len(twinkles) > 0) and (utime.ticks_diff(utime.ticks_ms(),twinkles[0]["starttime"]) > twinkle_duration_ms * 2):
            twinkles.pop(0)
        
        await pixels_show()
        await uasyncio.sleep(0)


async def twinkling(next_button_pressed, twinkles, ticks, cherry=False):

    pause_fixed_ms = 50
    pause_max_variable_ms = 200
    twinkle_duration_ms = 700

    if not cherry:
        red = 0
        green = 255
        blue = 0
    else:
        red = 232
        green = 50
        blue = 135

    # TODO: make pause a feature of each twinkle
    pause = random.randrange(pause_max_variable_ms)

    while not next_button_pressed.is_set():

        for led in range(NUM_LEDS):
            pixels_set(led, (
                (red*brightness[led]) // 255,
                (green*brightness[led]) // 255,
                (blue*brightness[led]) // 255
            ))

        # select a LED and make sure it isn't already twinkling
        dice = random.randrange(NUM_LEDS)
        while True:
            existing_twinkles = filter(lambda item: item["position"] == dice, twinkles)
            if all(False for _ in existing_twinkles):
                break
            dice = random.randrange(NUM_LEDS)

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
            green_component = 255 - abs(((offset-twinkle_duration_ms) * (255-brightness[twinkle["position"]])) // twinkle_duration_ms)
            pixels_set(twinkle["position"], (max(red_blue_component,0),max(green_component,brightness[twinkle["position"]]),max(red_blue_component,0)))
        
        while (len(twinkles) > 0) and (utime.ticks_diff(utime.ticks_ms(),twinkles[0]["starttime"]) > twinkle_duration_ms * 2):
            twinkles.pop(0)
        
        await pixels_show()
        await uasyncio.sleep(0)


async def fadeout(twinkles, ticks):

    FADEOUT_TIME_MS = 800
    red = 232
    green = 50
    blue = 135

    fade_start_ticks = utime.ticks_ms()
    fade = max(FADEOUT_TIME_MS - utime.ticks_diff(utime.ticks_ms(), fade_start_ticks), 0)
    while fade > 0:
        for led in range(NUM_LEDS):
            pixels_set(led, (
                (red*brightness[led]*fade) // (255*FADEOUT_TIME_MS),
                (green*brightness[led]*fade) // (255*FADEOUT_TIME_MS),
                (blue*brightness[led]*fade) // (255*FADEOUT_TIME_MS)
            ))
        await pixels_show()
        await uasyncio.sleep(0)
        fade = max(FADEOUT_TIME_MS - utime.ticks_diff(utime.ticks_ms(), fade_start_ticks), 0)

    pixels_fill((0,0,0)) 
    await pixels_show()


async def enchanted_forest_base(lcd, next_button_pressed):
    lcd.print_lcd("Enchanted Forest")
    lcd.setCursor(0,1)
    lcd.printout("FADE IN")
    await uasyncio.sleep(0)

    ticks = utime.ticks_ms()
    diff = 0

    while diff < 2000:
        diff = utime.ticks_diff(utime.ticks_ms(), ticks)
        for led in range(NUM_LEDS):
            pixels_set(led, (0,(brightness[led] * diff) // 2000,0))
        await pixels_show()
        await uasyncio.sleep(0)

    twinkles = []

    # TODO: Make LCD write async or use the other core
    lcd.print_lcd("Enchanted Forest")
    lcd.setCursor(0,1)
    lcd.printout("SLOW")
    await twinkling(next_button_pressed, twinkles, ticks)

    next_button_pressed.clear()
    lcd.print_lcd("Enchanted Forest")
    lcd.setCursor(0,1)
    lcd.printout("CEST LA VIE")
    await fast_sequence(next_button_pressed, twinkles, ticks)

    next_button_pressed.clear()
    lcd.print_lcd("Enchanted Forest")
    lcd.setCursor(0,1)
    lcd.printout("FREEZE")

    # set fixed Freeze position
    red = 0
    green = 255
    blue = 0
    for led in range(NUM_LEDS):
        if (led % 10) != 0:
            pixels_set(led, (
                (brightness[led] * red) // 255,
                (brightness[led] * green) // 255,
                (brightness[led] * blue) // 255
            ))
        else:
            pixels_set(led, (255, 255, 255))
    await pixels_show()
    while not next_button_pressed.is_set():
        await uasyncio.sleep(0)

    # setup twinkles array for fadeout
    ticks = utime.ticks_ms() - 700
    twinkles = []
    for led in range(0, NUM_LEDS, 10):
        twinkles.append({
            "starttime": ticks,
            "position": led,
        })
    ticks = utime.ticks_ms()

    next_button_pressed.clear()
    lcd.print_lcd("Enchanted Forest")
    lcd.setCursor(0,1)
    lcd.printout("RESTART SLOW")
    await twinkling(next_button_pressed, twinkles, ticks)

    # fade from greens to cherry blossom
    lcd.print_lcd("Enchanted Forest")
    lcd.setCursor(0,1)
    lcd.printout("FADE TO CHERRY")
    cherry_red = 232
    cherry_green = 50
    cherry_blue = 135
    fade_start_ticks = utime.ticks_ms()
    FADE_DURATION = const(2000)
    fade = min(utime.ticks_diff(utime.ticks_ms(), fade_start_ticks), FADE_DURATION)
    while fade < FADE_DURATION:

        for led in range(NUM_LEDS):
            pixels_set(led, (
                ((red * (FADE_DURATION - fade)) + (cherry_red * fade)) * brightness[led] // (255 * FADE_DURATION),
                ((green * (FADE_DURATION - fade)) + (cherry_green * fade)) * brightness[led] // (255 * FADE_DURATION),
                ((blue * (FADE_DURATION - fade)) + (cherry_blue * fade)) * brightness[led] // (255 * FADE_DURATION),
            ))
        await pixels_show()
        await uasyncio.sleep(0)
        fade = min(utime.ticks_diff(utime.ticks_ms(), fade_start_ticks), FADE_DURATION)

    twinkles = []

    next_button_pressed.clear()
    lcd.print_lcd("Enchanted Forest")
    lcd.setCursor(0,1)
    lcd.printout("CHERRY BLOSSOM")
    await twinkling(next_button_pressed, twinkles, ticks, cherry=True)

    next_button_pressed.clear()
    lcd.print_lcd("Enchanted Forest")
    lcd.setCursor(0,1)
    lcd.printout("FADEOUT")
    await fadeout(twinkles, ticks)

    lcd.print_lcd("OFF")

import array
from machine import Pin
from micropython import const
import rp2
import uasyncio
import utime
import random
import gc

PIN_NUM = const(22)

# Configure the number of WS2812 LEDs.
NUM_LEDS = const(300)  # must be a multiple of GROUP_SIZE
GROUP_SIZE = const(30)

BRIGHTNESSES = array.array("I", [30, 100, 200, 255, 200, 100])

FOREST_RED = const(0)
FOREST_GREEN = const(255)
FOREST_BLUE = const(0)

CHERRY_RED = const(208)
CHERRY_GREEN = const(45)
CHERRY_BLUE = const(121)

FAST_SEQUENCE_PERIOD_MS = const(750)
FAST_SEQUENCE_TWINKLE_DURATION_MS = const(200)

TWINKLING_PERIOD_FIXED_MS = const(20)
TWINKLING_PERIOD_MAX_VARIABLE_MS = const(100)
TWINKLING_DURATION_MS = const(700)  # this is the half-period

FADE_IN_DURATION_MS = const(2000)
FADEOUT_TIME_MS = const(800)
FADE_TO_CHERRY_DURATION = const(2000)

TWINKLE_COLOURS_RED = [255, 255, 255]
TWINKLE_COLOURS_GREEN = [255, 54, 230]
TWINKLE_COLOURS_BLUE = [255, 158, 0]
TWINKLE_COLOUR = 1

brightness = array.array("I", [0 for _ in range(NUM_LEDS)])
for led in range(NUM_LEDS):
    brightness[led] = BRIGHTNESSES[led % 6]


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


async def fast_sequence(next_button_pressed, twinkles, ticks):
    red = FOREST_RED
    green = FOREST_GREEN
    blue = FOREST_BLUE

    next_led = 5

    while not next_button_pressed.is_set():
        for led in range(NUM_LEDS):
            pixels_set(led, (
                (red*brightness[led]) // 255,
                (green*brightness[led]) // 255,
                (blue*brightness[led]) // 255
            ))

        if utime.ticks_diff(utime.ticks_ms(), ticks) >= FAST_SEQUENCE_PERIOD_MS:
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
            red_blue_component = 255 - abs(((offset-FAST_SEQUENCE_TWINKLE_DURATION_MS) * 255) // FAST_SEQUENCE_TWINKLE_DURATION_MS)
            green_component = 255 - abs(((offset-FAST_SEQUENCE_TWINKLE_DURATION_MS) * (255-brightness[twinkle["position"]])) // FAST_SEQUENCE_TWINKLE_DURATION_MS)
            pixels_set(twinkle["position"], (max(red_blue_component,0),max(green_component,brightness[twinkle["position"]]),max(red_blue_component,0)))
        
        while (len(twinkles) > 0) and (utime.ticks_diff(utime.ticks_ms(),twinkles[0]["starttime"]) > FAST_SEQUENCE_TWINKLE_DURATION_MS * 2):
            twinkles.pop(0)
        
        await pixels_show()
        await uasyncio.sleep(0)


async def twinkling(next_button_pressed, twinkles, ticks, cherry=False):
    if not cherry:
        red = FOREST_RED
        green = FOREST_GREEN
        blue = FOREST_BLUE
    else:
        red = CHERRY_RED
        green = CHERRY_GREEN
        blue = CHERRY_BLUE

    # TODO: make pause a feature of each twinkle
    pause = random.randrange(TWINKLING_PERIOD_MAX_VARIABLE_MS)

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

        if utime.ticks_diff(utime.ticks_ms(), ticks) > TWINKLING_PERIOD_FIXED_MS + pause:
            twinkles.append({
                "starttime": utime.ticks_ms(),
                "position": dice,
            })
            ticks = utime.ticks_ms()
            pause = random.randrange(TWINKLING_PERIOD_MAX_VARIABLE_MS)

        for twinkle in twinkles:
            offset = utime.ticks_diff(utime.ticks_ms(),twinkle["starttime"])
            red_component = 255 - abs(((offset-TWINKLING_DURATION_MS) * (255-(red*brightness[twinkle["position"]]//255))) // TWINKLING_DURATION_MS)
            green_component = 255 - abs(((offset-TWINKLING_DURATION_MS) * (255-(green*brightness[twinkle["position"]]//255))) // TWINKLING_DURATION_MS)
            blue_component = 255 - abs(((offset-TWINKLING_DURATION_MS) * (255-(blue*brightness[twinkle["position"]]//255))) // TWINKLING_DURATION_MS)
            pixels_set(twinkle["position"], (max(red_component,0),max(green_component,0),max(blue_component,0)))
        
        while (len(twinkles) > 0) and (utime.ticks_diff(utime.ticks_ms(),twinkles[0]["starttime"]) > TWINKLING_DURATION_MS * 2):
            twinkles.pop(0)
        
        await pixels_show()
        await uasyncio.sleep(0)


async def fadeout(twinkles, ticks):

    red = CHERRY_RED
    green = CHERRY_GREEN
    blue = CHERRY_BLUE

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

    while diff < FADE_IN_DURATION_MS:
        diff = utime.ticks_diff(utime.ticks_ms(), ticks)
        for led in range(NUM_LEDS):
            pixels_set(led, (
                0,
                min((brightness[led] * diff) // FADE_IN_DURATION_MS, 255)
                ,0
            ))
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
    red = FOREST_RED
    green = FOREST_GREEN
    blue = FOREST_BLUE
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
    ticks = utime.ticks_ms() - TWINKLING_DURATION_MS
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
    cherry_red = CHERRY_RED
    cherry_green = CHERRY_GREEN
    cherry_blue = CHERRY_BLUE
    fade_start_ticks = utime.ticks_ms()
    fade = min(utime.ticks_diff(utime.ticks_ms(), fade_start_ticks), FADE_TO_CHERRY_DURATION)
    while fade < FADE_TO_CHERRY_DURATION:

        for led in range(NUM_LEDS):
            pixels_set(led, (
                ((red * (FADE_TO_CHERRY_DURATION - fade)) + (cherry_red * fade)) * brightness[led] // (255 * FADE_TO_CHERRY_DURATION),
                ((green * (FADE_TO_CHERRY_DURATION - fade)) + (cherry_green * fade)) * brightness[led] // (255 * FADE_TO_CHERRY_DURATION),
                ((blue * (FADE_TO_CHERRY_DURATION - fade)) + (cherry_blue * fade)) * brightness[led] // (255 * FADE_TO_CHERRY_DURATION),
            ))
        await pixels_show()
        await uasyncio.sleep(0)
        fade = min(utime.ticks_diff(utime.ticks_ms(), fade_start_ticks), FADE_TO_CHERRY_DURATION)

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


async def twinkling_only(lcd, next_button_pressed):
    lcd.print_lcd("Twinkles only")
    lcd.setCursor(0,1)
    lcd.printout("TWINKLING")
    await uasyncio.sleep(0)

    ticks = utime.ticks_ms()
    twinkles = []
    pause = random.randrange(TWINKLING_PERIOD_MAX_VARIABLE_MS)

    pixels_fill((0,0,0))
    await pixels_show()

    while not next_button_pressed.is_set():
        dice = random.randrange(NUM_LEDS)

        while True:
            existing_twinkles = filter(lambda item: item["position"] == dice, twinkles)
            if all(False for _ in existing_twinkles):
                break
            dice = random.randrange(NUM_LEDS)

        if utime.ticks_diff(utime.ticks_ms(), ticks) > TWINKLING_PERIOD_FIXED_MS + pause:
            twinkles.append({
                "starttime": utime.ticks_ms() - TWINKLING_DURATION_MS // 4,
                "position": dice,
            })
            ticks = utime.ticks_ms()
            pause = random.randrange(TWINKLING_PERIOD_MAX_VARIABLE_MS)

        for twinkle in twinkles:
            offset = utime.ticks_diff(utime.ticks_ms(), twinkle["starttime"])
            red_component = TWINKLE_COLOURS_RED[TWINKLE_COLOUR] - abs(((offset-TWINKLING_DURATION_MS) * TWINKLE_COLOURS_RED[TWINKLE_COLOUR]) // TWINKLING_DURATION_MS)
            green_component = TWINKLE_COLOURS_GREEN[TWINKLE_COLOUR] - abs(((offset-TWINKLING_DURATION_MS) * TWINKLE_COLOURS_GREEN[TWINKLE_COLOUR]) // TWINKLING_DURATION_MS)
            blue_component = TWINKLE_COLOURS_BLUE[TWINKLE_COLOUR] - abs(((offset-TWINKLING_DURATION_MS) * TWINKLE_COLOURS_BLUE[TWINKLE_COLOUR]) // TWINKLING_DURATION_MS)
            pixels_set(twinkle["position"], (max(red_component,0),max(green_component,0),max(blue_component,0)))
        
        while (len(twinkles) > 0) and (utime.ticks_diff(utime.ticks_ms(),twinkles[0]["starttime"]) > TWINKLING_DURATION_MS * 2):
            twinkles.pop(0)
        
        await pixels_show()
        await uasyncio.sleep(0)

    next_button_pressed.clear()
    lcd.print_lcd("Twinkling only")
    lcd.setCursor(0,1)
    lcd.printout("CEST LA VIE")

    next_led = 5
    while not next_button_pressed.is_set():
        if utime.ticks_diff(utime.ticks_ms(), ticks) >= FAST_SEQUENCE_PERIOD_MS:
            for i in range(0, NUM_LEDS, GROUP_SIZE):
                twinkles.append({
                    "starttime": utime.ticks_ms() - TWINKLING_DURATION_MS // 4,
                    "position": next_led + i,
                })
                twinkles.append({
                    "starttime": utime.ticks_ms() - TWINKLING_DURATION_MS // 4,
                    "position": next_led + i + 2,
                })
            ticks = utime.ticks_ms()
            next_led = (next_led + 10) % GROUP_SIZE

        for twinkle in twinkles:
            offset = utime.ticks_diff(utime.ticks_ms(), twinkle["starttime"])
            red_component = TWINKLE_COLOURS_RED[TWINKLE_COLOUR] - abs(((offset-TWINKLING_DURATION_MS) * TWINKLE_COLOURS_RED[TWINKLE_COLOUR]) // TWINKLING_DURATION_MS)
            green_component = TWINKLE_COLOURS_GREEN[TWINKLE_COLOUR] - abs(((offset-TWINKLING_DURATION_MS) * TWINKLE_COLOURS_GREEN[TWINKLE_COLOUR]) // TWINKLING_DURATION_MS)
            blue_component = TWINKLE_COLOURS_BLUE[TWINKLE_COLOUR] - abs(((offset-TWINKLING_DURATION_MS) * TWINKLE_COLOURS_BLUE[TWINKLE_COLOUR]) // TWINKLING_DURATION_MS)
            pixels_set(twinkle["position"], (max(red_component,0),max(green_component,0),max(blue_component,0)))
        
        while (len(twinkles) > 0) and (utime.ticks_diff(utime.ticks_ms(),twinkles[0]["starttime"]) > TWINKLING_DURATION_MS * 2):
            twinkles.pop(0)
        
        await pixels_show()
        await uasyncio.sleep(0)

    next_button_pressed.clear()
    lcd.print_lcd("Twinkling only")
    lcd.setCursor(0,1)
    lcd.printout("FREEZE")

    for led in range(NUM_LEDS):
        if (led % 10) == 0:
            pixels_set(led, (
                TWINKLE_COLOURS_RED[TWINKLE_COLOUR],
                TWINKLE_COLOURS_GREEN[TWINKLE_COLOUR],
                TWINKLE_COLOURS_BLUE[TWINKLE_COLOUR]
            ))
        else:
            pixels_set(led, (0,0,0))
    await pixels_show()
    while not next_button_pressed.is_set():
        await uasyncio.sleep(0)

    ticks = utime.ticks_ms() - TWINKLING_DURATION_MS
    twinkles = []
    for led in range(0, NUM_LEDS, 10):
        twinkles.append({
            "starttime": ticks,
            "position": led,
        })
    ticks = utime.ticks_ms()

    next_button_pressed.clear()
    lcd.print_lcd("Twinkling only")
    lcd.setCursor(0,1)
    lcd.printout("RESTART TWINKLE")

    while not next_button_pressed.is_set():
        dice = random.randrange(NUM_LEDS)

        while True:
            existing_twinkles = filter(lambda item: item["position"] == dice, twinkles)
            if all(False for _ in existing_twinkles):
                break
            dice = random.randrange(NUM_LEDS)

        if utime.ticks_diff(utime.ticks_ms(), ticks) > TWINKLING_PERIOD_FIXED_MS + pause:
            twinkles.append({
                "starttime": utime.ticks_ms() - TWINKLING_DURATION_MS // 4,
                "position": dice,
            })
            ticks = utime.ticks_ms()
            pause = random.randrange(TWINKLING_PERIOD_MAX_VARIABLE_MS)

        for twinkle in twinkles:
            offset = utime.ticks_diff(utime.ticks_ms(), twinkle["starttime"])
            red_component = TWINKLE_COLOURS_RED[TWINKLE_COLOUR] - abs(((offset-TWINKLING_DURATION_MS) * TWINKLE_COLOURS_RED[TWINKLE_COLOUR]) // TWINKLING_DURATION_MS)
            green_component = TWINKLE_COLOURS_GREEN[TWINKLE_COLOUR] - abs(((offset-TWINKLING_DURATION_MS) * TWINKLE_COLOURS_GREEN[TWINKLE_COLOUR]) // TWINKLING_DURATION_MS)
            blue_component = TWINKLE_COLOURS_BLUE[TWINKLE_COLOUR] - abs(((offset-TWINKLING_DURATION_MS) * TWINKLE_COLOURS_BLUE[TWINKLE_COLOUR]) // TWINKLING_DURATION_MS)
            pixels_set(twinkle["position"], (max(red_component,0),max(green_component,0),max(blue_component,0)))
        
        while (len(twinkles) > 0) and (utime.ticks_diff(utime.ticks_ms(),twinkles[0]["starttime"]) > TWINKLING_DURATION_MS * 2):
            twinkles.pop(0)
        
        await pixels_show()
        await uasyncio.sleep(0)

    next_button_pressed.clear()
    lcd.print_lcd("Twinkling only")
    lcd.setCursor(0,1)
    lcd.printout("FADEOUT")

    while len(twinkles) > 0:
        for twinkle in twinkles:
            offset = utime.ticks_diff(utime.ticks_ms(), twinkle["starttime"])
            red_component = TWINKLE_COLOURS_RED[TWINKLE_COLOUR] - abs(((offset-TWINKLING_DURATION_MS) * TWINKLE_COLOURS_RED[TWINKLE_COLOUR]) // TWINKLING_DURATION_MS)
            green_component = TWINKLE_COLOURS_GREEN[TWINKLE_COLOUR] - abs(((offset-TWINKLING_DURATION_MS) * TWINKLE_COLOURS_GREEN[TWINKLE_COLOUR]) // TWINKLING_DURATION_MS)
            blue_component = TWINKLE_COLOURS_BLUE[TWINKLE_COLOUR] - abs(((offset-TWINKLING_DURATION_MS) * TWINKLE_COLOURS_BLUE[TWINKLE_COLOUR]) // TWINKLING_DURATION_MS)
            pixels_set(twinkle["position"], (max(red_component,0),max(green_component,0),max(blue_component,0)))
        
        while (len(twinkles) > 0) and (utime.ticks_diff(utime.ticks_ms(),twinkles[0]["starttime"]) > TWINKLING_DURATION_MS * 2):
            twinkles.pop(0)
        
        await pixels_show()
        await uasyncio.sleep(0)

    pixels_fill((0,0,0))
    await pixels_show()
    lcd.print_lcd("OFF")


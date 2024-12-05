import array
from machine import Pin
import rp2
import uasyncio
import utime
import random

# Configure the number of WS2812 LEDs.
NUM_LEDS = 200
PIN_NUM = 22
brightness = 1.0


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
        r = int(((c >> 8) & 0xFF) * brightness)
        g = int(((c >> 16) & 0xFF) * brightness)
        b = int((c & 0xFF) * brightness)
        dimmer_ar[i] = (g<<16) + (r<<8) + b
    sm.put(dimmer_ar, 8)
    await uasyncio.sleep_ms(10)


def pixels_set(i, color):
    ar[i] = (color[0]<<16) + (color[1]<<8) + color[2]


def pixels_fill(color):
    for i in range(len(ar)):
        pixels_set(i, color)


async def color_chase(color, wait):
    for i in range(NUM_LEDS):
        pixels_set(i, color)
        await uasyncio.sleep(wait)
        await pixels_show()
    await uasyncio.sleep(0.2)
 

def wheel(pos):
    # Input a value 0 to 255 to get a color value.
    # The colours are a transition r - g - b - back to r.
    if pos < 0 or pos > 255:
        return (0, 0, 0)
    if pos < 85:
        return (255 - pos * 3, pos * 3, 0)
    if pos < 170:
        pos -= 85
        return (0, 255 - pos * 3, pos * 3)
    pos -= 170
    return (pos * 3, 0, 255 - pos * 3)
 
 
async def rainbow_cycle(wait, color_range=range(255)):
    for j in color_range:
        for i in range(NUM_LEDS):
            rc_index = (i * len(color_range) // NUM_LEDS) + j
            pixels_set(i, wheel(rc_index & 255))
        await pixels_show()
        await uasyncio.sleep(wait)


async def rainbow_cycle_2(wait, color_range=list(range(255)), duration=10, speed=1, wavelength=1.0):
    start_time = utime.time()
    start_ticks = utime.ticks_ms()
    while utime.time() < start_time + duration:
        hue_offset = int(utime.ticks_diff(start_ticks, utime.ticks_ms()) * speed / 1000)
        for i in range(NUM_LEDS):
            arr_offset = (int(hue_offset + (i * wavelength))) % len(color_range)
            pixels_set(i, wheel(color_range[arr_offset]))
        await pixels_show()
        await uasyncio.sleep(wait)

def color(red: int, green: int, blue: int, white: int = 0):
    """Convert the provided red, green, blue color to a 24-bit color value.
    Each color component should be a value 0-255 where 0 is the lowest intensity
    and 255 is the highest intensity.

    Note the sequencing has been changed from RGB (most significant->least significant) to
    GRB - this seems to be a "feature" of the light strip I have!

    :param red: red component 0-255
    :param green: green component 0-255
    :param blue: blue component 0-255
    :param white: overall brightness, 0-255, defaults to 0
    :return:
    """
    return (white << 24) | (green << 16) | (red << 8) | blue

async def xmas_tree():
    twinkle_colours = [
        (255, 0, 0),
        (0, 0, 255),
        (255, 255, 0),
        (0, 255, 255),
        (255, 0, 127)
    ]

    XMAS_PATTERNS = {
        "trunk": [17, 18, 19, 37, 38, 39, 54, 55, 69, 70, 75, 90, 105],
        "base": list(range(0, 17)) + list(range(125, 143)),
        "star": list(range(71, 75)),
        "branches": list(range(20, 37)) + list(range(40, 54)) + list(range(56, 69)) +
                    list(range(76, 90)) + list(range(91, 105)) + list(range(106, 125))
    }

    effects = {"snowing": [], "twinkles": []}
    tickms = utime.ticks_ms()
    start_ticks = tickms

    while True:

        # add a twinkle
        if utime.ticks_diff(utime.ticks_ms(),tickms) > 10:
            dice = random.randrange(1, 200)
            if dice >= 20 and dice <= 148:
                effects["snowing"].append({"starttime": utime.ticks_ms(), "blue": False,
                                            "position": random.choice(XMAS_PATTERNS["base"])})
            elif dice >= 150 and dice <= 190:
                effects["snowing"].append({"starttime": utime.ticks_ms(), "blue": True,
                                            "position": random.choice(XMAS_PATTERNS["base"])})
            elif dice >= 1 and dice <= 15:
                effects["twinkles"].append(
                    {"starttime": utime.ticks_ms(), "position": random.choice(XMAS_PATTERNS["branches"]),
                        "colour": random.choice(twinkle_colours)})
            tickms = utime.ticks_ms()

        # trunk is static
        print("trunk")
        for i in XMAS_PATTERNS.get("trunk"):
            pixels_set(i, (150, 75, 0))

        # base snowing effect
        print("base")
        for i in XMAS_PATTERNS.get("base"):
            pixels_set(i, (20, 20, 20))

        print("snowing")
        for effect in effects["snowing"]:
            brightness = int((1 - abs((utime.ticks_diff(utime.ticks_ms(), effect["starttime"] // 1000)) * 2 - 1)) * (255-20) + 20)
            if brightness >= 20:
                if effect["blue"]:
                    pixels_set(effect["position"], (20, brightness, brightness))
                else:
                    pixels_set(effect["position"], (brightness, brightness, brightness))

        print("star")
        star_colour_comp = int(abs((utime.ticks_diff(utime.ticks_ms(), start_ticks) // 1000) % 2 - 1) * 255)
        for i in XMAS_PATTERNS.get("star"):
            pixels_set(i, (star_colour_comp, star_colour_comp, 0))

        print("tree")
        # christmas tree lights
        for i in XMAS_PATTERNS.get("branches"):
            pixels_set(i, (0, 255, 0))

        print("twinkles")
        for effect in effects["twinkles"]:
            pixels_set(effect["position"], effect["colour"])

        await pixels_show()
        await uasyncio.sleep(0)

        if effects["snowing"] != [] and utime.ticks_diff(utime.ticks_ms(),effects["snowing"][0]["starttime"]) > 1000:
            effects["snowing"].pop(0)

        if effects["twinkles"] != [] and utime.ticks_diff(utime.ticks_ms(),effects["twinkles"][0]["starttime"]) > 1000:
            effects["twinkles"].pop(0)

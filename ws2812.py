import array
from machine import Pin
from micropython import const
import rp2
import uasyncio
import utime
import random
import gc
import micropython

PIN_NUM = 22
NUM_LEDS = const(283)
STEP = 8

chance = 0


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


@micropython.native
async def starlight(lcd, next_button_pressed):

    numberofleds = NUM_LEDS
    prevchance = 0
    starttime = utime.ticks_ms()
    ledslist = [] # 0 to 128
    blueorwhite = [] # 1 or 2

    for i in range(numberofleds):
        ledslist.append(0)
        blueorwhite.append(1)
    
    while not next_button_pressed.is_set():
        global chance

        chance = max(1000-((utime.ticks_diff(utime.ticks_ms(),starttime))//300),600)
        if chance != prevchance:
            lcd.print_lcd(f"STARLIGHT {(1000-chance)//4}%")
            print("lcd changed")
            prevchance = chance

        print(chance)
        
        if random.randint(1,1000) > chance:
    
            num1 = random.randint(0,(numberofleds-1))
            if ledslist[num1] == 0: 
                ledslist[num1] = 318
                num2 = random.randint(1,2)
                blueorwhite[num1] = num2
            else:
                pass
            
        for i in range(numberofleds):
            
            if ledslist[i] > 254: # fade in if bigger than 254
                colour =  4 * abs(ledslist[i]-318)
                if blueorwhite[i] == 1:
                    pixels_set(i, ((colour,colour,colour)))
                else:
                    pixels_set(i, ((0,colour,colour)))
                    
            else: # else fade out if not bigger than 254 
                if blueorwhite[i] == 1: # fade out
                    pixels_set(i, ((ledslist[i],ledslist[i],ledslist[i])))
                else:
                    pixels_set(i, ((0,ledslist[i],ledslist[i])))
                    
        await pixels_show()
                
        for i in range(numberofleds):
            if ledslist[i] > STEP:
                ledslist[i] =  ledslist[i] - STEP
            if ledslist[i] <= STEP:
                ledslist[i] = 0

        await uasyncio.sleep(0.01)

    while True:

        lcd.print_lcd(f"STARLIGHT FADEOUT")
        for i in range(numberofleds):
            
            if ledslist[i] > 254: # fade in if bigger than 254
                colour =  4 * abs(ledslist[i]-318)
                if blueorwhite[i] == 1:
                    pixels_set(i, ((colour,colour,colour)))
                else:
                    pixels_set(i, ((0,colour,colour)))

            else: #if not bigger than 254 
                if blueorwhite[i] == 1: # fade out
                    pixels_set(i, ((ledslist[i],ledslist[i],ledslist[i])))
                else:
                    pixels_set(i, ((0,ledslist[i],ledslist[i])))
                    
        await pixels_show()
                
        for i in range(numberofleds):
            if ledslist[i] > STEP:
                ledslist[i] =  ledslist[i] - STEP
            if ledslist[i] <= STEP:
                ledslist[i] = 0
            
        await uasyncio.sleep(0.01)

import ws2812
import uasyncio
import machine
import random
import LCD1602
import math
import utime

# loop 0 = 0,20
# loop 1 = 21,38
# loop 2 = 39,54
# loop 3 = 55,71
# loop 4 = 72,89
# loop 5 = 90,105
# loop 6 = 106,124
# loop 7 = 125,140
# loop 8 = 141,157
# loop 9 = 158,174
# loop 10 = 175,191
# loop 11 = 192,209
# loop 12 = 210,228
# loop 13 = 229,248
# loop 14 = 249,264
# loop 15 = 265,283

loopstarts = [ 0,21,39,55,71, 90,106,125,142,158,175,192,210,229,249,265]
loopends =   [20,38,54,70,89,105,124,140,157,174,191,209,228,248,264,283]



def scale_colour(rgb,factor):
    return tuple(math.ceil(c / factor) for c in rgb)

BLACK = (0,0,0)
RED = scale_colour((255, 0, 0),16)
YELLOW = scale_colour((255, 150, 0),16)
GREEN = scale_colour((0, 255, 0),16)
CYAN = scale_colour((0, 255, 255),16)
BLUE = scale_colour((0, 0, 255),16)
PURPLE = scale_colour((180, 0, 255),16)
WHITE = scale_colour((255, 255, 255),16)

COLORS = (BLACK, RED, YELLOW, GREEN, CYAN, BLUE, PURPLE, WHITE)

async def black():
    try:
        ws2812.pixels_fill((0,0,0))
        print("lights off")
        await ws2812.pixels_show()
        
    except uasyncio.CancelledError:
        pass


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
        
        for j in range(len(loopstarts)):
            
            while randnum  == prevrandnum:
                randnum = random.randint(0,100) % 7 + 1
            
            await loop_filler(j, COLORS[randnum])
            
            prevrandnum = randnum
            
        prevrandnum = 0
        
        await ws2812.pixels_show()
        print("Colours shown")
        await uasyncio.sleep(0.85)

        
    except uasyncio.CancelledError:
        pass


# async def main():
#     running_task = uasyncio.create_task(loop_filler(int(input("loop num? ")),int(input("colour num? "))))
#     await running_task

async def main():
#     running_task = uasyncio.create_task(black())
#     await running_task
#     running_task.cancel()
    running_task = uasyncio.create_task(colour_loop())
    await running_task
#     utime.sleep(0.5)
#     running_task.cancel()
#     running_task = uasyncio.create_task(black())
#     await running_task
    

if __name__ == "__main__":
    while True:
        uasyncio.run(main())
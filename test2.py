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

lightssf = 0

def scale_color(rgb,factor):
    return tuple(math.ceil(c * factor) for c in rgb)

originallightssf = 1

BLACK = (0,0,0)
RED = scale_color((255, 0, 0),originallightssf)
YELLOW = scale_color((255, 150, 0),originallightssf)
GREEN = scale_color((0, 255, 0),originallightssf)
CYAN = scale_color((0, 255, 255),originallightssf)
BLUE = scale_color((0, 0, 255),originallightssf)
PURPLE = scale_color((180, 0, 255),originallightssf)
WHITE = scale_color((255, 255, 255),originallightssf)

COLORS = (BLACK, RED, YELLOW, GREEN, CYAN, BLUE, PURPLE, WHITE)




async def blank():
    try:
        ws2812.pixels_fill((0,0,0))
        print("lights off")
        await ws2812.pixels_show()
        
    except uasyncio.CancelledError:
        pass


async def loop_filler(loopnum,colornum):
    try:
        
        for i in range(loopstarts[loopnum],loopends[loopnum]):
            
            ws2812.pixels_set(i, scale_color(colornum,lightssf))
            
    except uasyncio.CancelledError:
        pass

async def color_loop():
    
    randnum = random.randint(0,100) % 7 + 1
    prevrandnum = 0
    
    global lightssf
    
    try:
        while True:
            
            for i in range(len(loopstarts)):
                if lightssf < 1:
                    lightssf = lightssf + 0.1
                    print(lightssf)
                        
                    while randnum == prevrandnum:
                        randnum = random.randint(0,100) % 7 + 1
                    
                    print(scale_color(COLORS[randnum],lightssf))
                    
                    await loop_filler(i, scale_color(COLORS[randnum],lightssf))
                    
            
            for j in range(len(loopstarts)):
                
                while randnum == prevrandnum:
                    randnum = random.randint(0,100) % 7 + 1
                
                await loop_filler(j, scale_color(COLORS[randnum],lightssf))
                
                prevrandnum = randnum
                
            prevrandnum = 0
            
            await ws2812.pixels_show()
            print("colors shown")
            await uasyncio.sleep(0.85)
        
        for i in range(len(loopstarts)):
                if lightssf > 0:
                    lightssf =- 0.1
        
    except uasyncio.CancelledError:
        pass


# async def main():
#     running_task = uasyncio.create_task(loop_filler(int(input("loop num? ")),int(input("color num? "))))
#     await running_task

async def main():
#     running_task = uasyncio.create_task(blank())
#     await running_task
#     running_task.cancel()
    running_task = uasyncio.create_task(color_loop())
    await running_task
#     utime.sleep(0.5)
#     running_task.cancel()
#     running_task = uasyncio.create_task(blank())
#     await running_task
    

if __name__ == "__main__":
    try:
        uasyncio.run(main())
    except KeyboardInterrupt:
        uasyncio.run(blank())
        #print("clearing screen")
        #lcd.print_lcd("")
        #utime.sleep(3)
        #print("exiting")

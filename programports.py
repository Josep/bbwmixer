import os
import sys
import mmap
import struct
import time

class ProgPorts():

    def tlog(self, x, ym=0.85, step=1/255):
        b = (-1+1/ym)**2
        a = 1/(b-1)
        y = a*b**(x*step)-a
        return int(round(y/step))

    def muxset(self,addr,out=True):
        GPIOMUXMODEOUT = 0x0f
        GPIOMUXMODEIN = 0x2f
        self.mm.seek(addr)
        if out:
            self.mm.write(struct.pack('<L', GPIOMUXMODEOUT))
        else:
            self.mm.write(struct.pack('<L', GPIOMUXMODEIN))

    def setpin(self,gpio, pin, clear=False):
        GPIOMEM = [(0x44E07000, 0x1000),   #(addr, size) GPIO0, pag 210 spruh73c.pdf
                   (0x4804C000, 0x1000),
                   (0x481AC000, 0x1000),
                   (0x481AE000, 0x1000)]
        GPIO_CLEARDATAOUT = 0x190
        GPIO_SETDATAOUT = 0x194
        fdm = os.open("/dev/mem", os.O_RDWR | os.O_SYNC)
        mm = mmap.mmap(fdm, GPIOMEM[gpio][1], mmap.MAP_SHARED, mmap.PROT_READ | mmap.PROT_WRITE, 0, GPIOMEM[gpio][0])
        if clear:
            mm[GPIO_CLEARDATAOUT:GPIO_CLEARDATAOUT+4] = struct.pack("<L", 1<<pin)
        else:
            mm[GPIO_SETDATAOUT:GPIO_SETDATAOUT+4] = struct.pack("<L", 1<<pin)
        mm.close()
        os.close(fdm)

    def readpin(self,gpio, pin):
        GPIOMEM = [(0x44E07000, 0x1000),   #(addr, size) GPIO0, pag 210 spruh73c.pdf
                   (0x4804C000, 0x1000),
                   (0x481AC000, 0x1000),
                   (0x481AE000, 0x1000)]
        GPIO_DATAIN = 0x138
        fdm = os.open("/dev/mem", os.O_RDWR | os.O_SYNC)
        mm = mmap.mmap(fdm, GPIOMEM[gpio][1], mmap.MAP_SHARED, mmap.PROT_READ | mmap.PROT_WRITE, 0, GPIOMEM[gpio][0])
        mm.seek(GPIO_DATAIN)
        u = struct.unpack('<L', mm.read(4))[0]
        u = u & (1 << pin)
        mm.close()
        os.close(fdm)
        return u>0

    def send(self, b, cs=0, wl=16):
        assert((cs >=0) and (cs<4) and ((wl==8) or (wl==16)))
        css = [(3,17),(1,19),(0,31),(1,18)]
        toreturn = 0
        #CS DOWN
        self.setpin(*css[cs],True)
        for i in range(wl-1,-1,-1):
            u = b & (1<<i)
            #SDI
            self.setpin(3,15,u==0)
            #CLK UP
            self.setpin(3,14)
            #SDO
            if self.readpin(3,16):
                toreturn = toreturn | (1<<i)
            #CLK DOWN
            self.setpin(3,14,True)
        #CS UP
        self.setpin(*css[cs])
        return toreturn

    def send2311(self, b):
        #CS DOWN
        self.setpin(0,5,True)
        for i in range(15,-1,-1):
            u = b & (1<<i)
            #SDI
            self.setpin(0,3,u==0)
            #CLK UP
            self.setpin(0,2)
            time.sleep(0.001)
            #CLK DOWN
            self.setpin(0,2,True)
        #CS UP
        self.setpin(0,5)

    def __init__(self):
        #pinmux       
        fdm = os.open("/dev/mem", os.O_RDWR | os.O_SYNC)
        self.mm = mmap.mmap(fdm, 0x2000, mmap.MAP_SHARED, mmap.PROT_READ | mmap.PROT_WRITE, 0, 0x44e10000)
        self.muxset(0x878)  #ZCEM gpio1_28 P9_12
        self.muxset(0x840)  #SHDN0 gpio1_16 P9_15
        self.muxset(0x844)  #SHDN1 gpio1_17 P9_23
        self.muxset(0x9ac)  #SHDN2 gpio3_21 P9_25
        self.muxset(0x9a4)  #SHDN3 gpio3_19 P9_27
        self.muxset(0x870)  #MUTE gpio0_30 P9_11
        self.muxset(0x84c)  #CS1 gpio1_19 P9_16
        self.muxset(0x874)  #CS2 gpio0_31 P9_13
        self.muxset(0x848)  #CS3 gpio1_18 P9_14
        self.muxset(0x964,False)  #midiin gpio0_7 P9_42 (INPUT)
        self.muxset(0x99c)  #spi1_cs0 gpio3_17 P9_28
        self.muxset(0x994)  #spi1_d0 gpio3_15 P9_29 (OUTPUT)
        self.muxset(0x998,False)  #spi1_d1 gpio3_16 P9_30 (INPUT)
        self.muxset(0x990)  #spi1_clk gpio3_14 P9_31
        self.muxset(0x95c)  #spi0_cs0 gpio0_5 P9_17
        self.muxset(0x958,False)  #spi0_d1 gpio0_4 P9_18(INPUT)
        self.muxset(0x954)  #spi0_d0 gpio0_3 P9_21(OUTPUT)
        self.muxset(0x950)  #spi0_clk gpio0_2 P9_22
        self.mm.close()
        os.close(fdm)
        #OE
        #GPIO0
        fdm = os.open("/dev/mem", os.O_RDWR | os.O_SYNC)
        mm = mmap.mmap(fdm, 0x1000, mmap.MAP_SHARED, mmap.PROT_READ | mmap.PROT_WRITE, 0, 0x44e07000)
        mm.seek(0x134)
        vactual = struct.unpack('<L', mm.read(4))[0]
        vfuturo = vactual & ~(1<<30)
        vfuturo = vfuturo & ~(1<<31)
        vfuturo = vfuturo & ~(1<<5)
        vfuturo = vfuturo & ~(1<<3)
        vfuturo = vfuturo & ~(1<<2)
        vfuturo = vfuturo | (1<<7)
        vfuturo = vfuturo | (1<<4)
        mm.seek(0x134)
        mm.write(struct.pack('<L', vfuturo))
        mm.close()
        os.close(fdm)
        #GPIO1
        fdm = os.open("/dev/mem", os.O_RDWR | os.O_SYNC)
        mm = mmap.mmap(fdm, 0x1000, mmap.MAP_SHARED, mmap.PROT_READ | mmap.PROT_WRITE, 0, 0x4804c000)
        mm.seek(0x134)
        vactual = struct.unpack('<L', mm.read(4))[0]
        vfuturo = vactual & ~(1<<28)
        vfuturo = vfuturo & ~(1<<16)
        vfuturo = vfuturo & ~(1<<17)
        vfuturo = vfuturo & ~(1<<18)
        vfuturo = vfuturo & ~(1<<19)
        mm.seek(0x134)
        mm.write(struct.pack('<L', vfuturo))
        mm.close()
        os.close(fdm)
        #GPIO3
        fdm = os.open("/dev/mem", os.O_RDWR | os.O_SYNC)
        mm = mmap.mmap(fdm, 0x1000, mmap.MAP_SHARED, mmap.PROT_READ | mmap.PROT_WRITE, 0, 0x481ae000)
        mm.seek(0x134)
        vactual = struct.unpack('<L', mm.read(4))[0]
        vfuturo = vactual & ~(1<<21)
        vfuturo = vfuturo & ~(1<<19)
        vfuturo = vfuturo & ~(1<<17)
        vfuturo = vfuturo & ~(1<<15)
        vfuturo = vfuturo & ~(1<<14)
        vfuturo = vfuturo | (1<<16)
        mm.seek(0x134)
        mm.write(struct.pack('<L', vfuturo))
        mm.close()
        os.close(fdm)
        #ZCEN,CS,SHDN to 1
        self.setpin(1,28) #ZCEN
        self.setpin(0,30) #MUTE
        self.setpin(3,17) #CS0
        self.setpin(1,19) #CS1
        self.setpin(0,31) #CS2
        self.setpin(1,18) #CS3
        self.setpin(1,16) #SHDN0
        self.setpin(1,17) #SHDN1
        self.setpin(3,21) #SHDN2
        self.setpin(3,19) #SHDN3
        self.setpin(3,14,True) #spi1_clk
        self.setpin(3,15,True) #spi1_d1
        self.setpin(0,5) #spi0_cs0
        self.setpin(0,2,True) #spi0_clk
        self.setpin(0,3,True) #spi0_d0

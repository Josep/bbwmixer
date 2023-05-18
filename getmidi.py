import os
import sys 
import mmap
import time
import struct
import signal
import threading
import programports

SHARRAM  = (0x4a310000, 0x3000)         #(addr,size) pag 19 am335xPruReferenceGuide.pdf
BUFSTART = 0x0020
BUFEND = 0x0ff4

class GetMidi(threading.Thread):
    def process(self, byt):
        #print("process: %d"%(byt))
        if self.state == 0:
            if byt in [0xB0, 0xBA]: 
                self.state = 1
                self.threebytes = [byt]
        elif self.state == 1:
            if byt in [0x07,0x44,0x46,0x47,0x48,0x49,0x4A,0x4B,0x4C]:
                self.state = 2
                self.threebytes.append(byt)
            else:
                self.state = 0
                self.threebytes = []
        elif self.state == 2:
            if 0 <= byt <= 127:
                self.threebytes.append(byt)
                if self.threebytes[0:2] == [0xB0, 0x44]:
                    print("Main Mute %02X" % self.threebytes[2]) 
                    self.pp.setpin(*(0,30), self.threebytes[2]==0x7f)
                elif self.threebytes[0:2] == [0xBA, 0x46]:
                    print("Mute channel 1 %02X" % self.threebytes[2]) 
                    self.pp.setpin(*(1,16), self.threebytes[2]==0x7f)
                elif self.threebytes[0:2] == [0xBA, 0x47]:
                    print("Mute channel 2 %02X" % self.threebytes[2]) 
                    self.pp.setpin(*(1,17), self.threebytes[2]==0x7f)
                elif self.threebytes[0:2] == [0xBA, 0x48]:
                    print("Mute channel 3 %02X" % self.threebytes[2])
                    self.pp.setpin(*(3,21), self.threebytes[2]==0x7f)
                elif self.threebytes[0:2] == [0xBA, 0x49]:
                    print("Mute channel 4 %02X" % self.threebytes[2])
                    self.pp.setpin(*(3,19), self.threebytes[2]==0x7f)
                elif self.threebytes[0:2] == [0xB0, 0x07]:
                    print("Main Volume %02X" % self.threebytes[2])
                    val = self.pp.tlog(self.threebytes[2]*2)
                    val2 = val
                    self.pp.send2311((val<<8)+val2)
                    self.st.ml = (val<<8)+val2
                elif self.threebytes[0:2] == [0xBA, 0x07]:
                    print("Channel 1 Volume %02X" % self.threebytes[2])
                    val = self.threebytes[2]*2
                    val2 = val
                    self.pp.send(val, cs=0)
                    self.st.c1l = val
                    self.pp.send(0x1000+val2, cs=0)
                    self.st.c1r = 0x1000+val2
                elif self.threebytes[0:2] == [0xBA, 0x4A]:
                    print("Channel 2 Volume %02X" % self.threebytes[2])
                    val = self.threebytes[2]*2
                    val2 = val
                    self.pp.send(val, cs=1)
                    self.st.c2l = val
                    self.pp.send(0x1000+val2, cs=1)
                    self.st.c2r = 0x1000+val2
                elif self.threebytes[0:2] == [0xBA, 0x4B]:
                    print("Channel 3 Volume %02X" % self.threebytes[2])
                    val = self.threebytes[2]*2
                    val2 = val
                    self.pp.send(val, cs=2)
                    self.st.c3l = val
                    self.pp.send(0x1000+val2, cs=2)
                    self.st.c3r = 0x1000+val2
                elif self.threebytes[0:2] == [0xBA, 0x4C]:
                    print("Channel 4 Volume %02X" % self.threebytes[2])
                    val = self.threebytes[2]*2
                    val2 = val
                    self.pp.send(val, cs=3)
                    self.st.c4l = val
                    self.pp.send(0x1000+val2, cs=3)
                    self.st.c4r = 0x1000+val2
                sys.stdout.flush()
                self.st.save()
            self.state = 0
            self.threebytes = []

    def run(self):
        #print("run")
        self.state = 0
        self.threebytes = []
        fdm3 = os.open("/dev/mem", os.O_RDWR | os.O_SYNC)
        mm3 = mmap.mmap(fdm3, SHARRAM[1], mmap.MAP_SHARED, mmap.PROT_READ | mmap.PROT_WRITE, 0, SHARRAM[0])
        while not self.abort:
            mm3.seek(0x00)
            iescr2 = struct.unpack('<L', mm3.read(4))[0]
            mm3.seek(0x04)
            ilect2 = struct.unpack('<L', mm3.read(4))[0]
            while (iescr2 != ilect2):
                #print("iescr2 != ilect2")
                mm3.seek(ilect2)
                byt = struct.unpack('<B', mm3.read(1))[0]
                mm3.seek(0x04)
                ilect2 = ilect2 + 1
                if ilect2 >= BUFEND:
                    ilect2 = BUFSTART
                mm3.write(struct.pack('<L', ilect2))
                self.process(byt)
        mm3.close()
        os.close(fdm3)        

    def begin(self, pp, st):
        #print("begin")
        self.pp = pp
        self.st = st
        #shram
        fdm = os.open("/dev/mem", os.O_RDWR | os.O_SYNC)
        mm = mmap.mmap(fdm, SHARRAM[1], mmap.MAP_SHARED, mmap.PROT_READ | mmap.PROT_WRITE, 0, SHARRAM[0])
        iescr2 = BUFSTART
        ilect2 = BUFSTART
        mm.seek(0x00)
        mm.write(struct.pack('<L', BUFSTART))  
        mm.seek(0x04)
        mm.write(struct.pack('<L', BUFSTART))  
        mm.seek(BUFSTART)
        for i in range(BUFSTART,BUFEND):
            mm.write(struct.pack('<c', bytes([0]))) 
        mm.close()
        os.close(fdm)
        self.abort = False
        self.start()

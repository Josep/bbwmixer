import sys
import os
import pickle
import asyncio
import tornado.web
import programports
import getmidi

class Status():
    def __init__(self):
        #read pickle file if exists
        self.picklefile = 'status.pickle'
        if os.path.isfile(self.picklefile):
            with open(self.picklefile,'rb') as f:
                self.__dict__ = pickle.load(f)
        else:
            self.m = 0xb8b8
            self.c1l = 0x007f
            self.c2l = 0x007f
            self.c3l = 0x007f
            self.c4l = 0x007f
            self.c1r = 0x107f
            self.c2r = 0x107f
            self.c3r = 0x107f
            self.c4r = 0x107f
            self.mute_m = 0
            self.mute_c1 = 0
            self.mute_c2 = 0
            self.mute_c3 = 0
            self.mute_c4 = 0
            self.zc_m = 0
            pickle.dump(self.__dict__,open(self.picklefile,'wb'))

    def save(self):
        pickle.dump(self.__dict__,open(self.picklefile,'wb'))
            
class SliderHandler(tornado.web.RequestHandler):

    def printarg(self, arg):
        val = self.get_argument(arg,None)
        if val != None:
            arg2 = arg[:-1]+'r'
            val2 = self.get_argument(arg2,None)
            print(arg, hex(int(val)), arg2, hex(int(val2)))
            if arg == 'ml':
                val = pp.tlog(int(val))
                val2 = pp.tlog(int(val2))
                pp.send2311((val<<8)+val2)
                st.ml = (val<<8)+val2
            if arg == 'c1l':
                pp.send(int(val), cs=0)
                st.c1l = int(val)
                pp.send(0x1000+int(val2), cs=0)
                st.c1r = 0x1000+int(val2)
            if arg == 'c2l':
                pp.send(int(val), cs=1)
                st.c2l = int(val)
                pp.send(0x1000+int(val2), cs=1)
                st.c2r = 0x1000+int(val2)
            if arg == 'c3l':
                pp.send(int(val), cs=2)
                st.c3l = int(val)
                pp.send(0x1000+int(val2), cs=2)
                st.c3r = 0x1000+int(val2)
            if arg == 'c4l':
                pp.send(int(val), cs=3)
                st.c4l = int(val)
                pp.send(0x1000+int(val2), cs=3)
                st.c4r = 0x1000+int(val2)
            st.save()

    def get(self):
        args = ['ml','c1l','c2l','c3l','c4l']
        for i in args:
            self.printarg(i)

class CheckBoxHandler(tornado.web.RequestHandler):
    def printarg(self, arg):
        val = self.get_argument(arg,None)
        if val != None:
            print(arg, val)
            pp.setpin(*self.dicc[arg],val=='true')

    def get(self):
        self.dicc = {'mute_m':(0,30),'mute_c1':(1,16),'mute_c2':(1,17),'mute_c3':(3,21),'mute_c4':(3,19),'zc_m':(1,28)}
        for i in self.dicc.keys():
            self.printarg(i)

def make_app():
    return tornado.web.Application([
        (r'/sliders', SliderHandler),
        (r'/checkboxes', CheckBoxHandler),
        (r"/(.*)", tornado.web.StaticFileHandler, {"path":"."}),
    ])

async def main():
    app = make_app()
    app.listen(80)
    shutdown_event = asyncio.Event()
    await shutdown_event.wait()

if __name__ == '__main__':
    #requirements
    if sys.version_info[0] != 3:
        sys.exit("python3 required")
    if os.geteuid() != 0:
        sys.exit("You need to have root privileges")
    st = Status()
    print('Program ports...')
    pp = programports.ProgPorts()
    pp.send2311(st.m)
    pp.send(st.c1l,cs=0)
    pp.send(st.c1r,cs=0)
    pp.send(st.c2l,cs=1)
    pp.send(st.c2r,cs=1)
    pp.send(st.c3l,cs=2)
    pp.send(st.c3r,cs=2)
    pp.send(st.c4l,cs=3)
    pp.send(st.c4r,cs=3)
    print("Starting midi reader...")
    gm = getmidi.GetMidi()
    gm.begin(pp,st)
    print("Starting web server...")
    asyncio.run(main())

import vlc
import sys
from random import choice
if sys.version_info[0] < 3:
    import Tkinter as Tk
    from Tkinter import ttk
    from Tkinter.filedialog import askdirectory
else:
    import tkinter as Tk
    from tkinter import ttk
    from tkinter.filedialog import askdirectory

import os
import pathlib
from threading import Thread, Event
import time
import platform
from pathlib import Path

class ttkTimer(Thread):
    def __init__(self, callback, tick):
        Thread.__init__(self)
        self.callback = callback
        self.stopFlag = Event()
        self.tick = tick
        self.iters = 0

    def run(self):
        while not self.stopFlag.wait(self.tick):
            self.iters += 1
            self.callback()

    def stop(self):
        self.stopFlag.set()

    def get(self):
        return self.iters

class Player(Tk.Frame):
    def __init__(self, parent, title=None):
        Tk.Frame.__init__(self, parent)
        self.parent = parent
        if title == None:
            title = "tk_vlc"
        self.parent.title(title)
        menubar = Tk.Menu(self.parent)
        self.parent.config(menu=menubar)
        fileMenu = Tk.Menu(menubar)
        fileMenu.add_command(label="Open", underline=0, command=self.OnOpen)
        fileMenu.add_command(label="Exit", underline=1, command=_quit)
        menubar.add_cascade(label="File", menu=fileMenu)
        self.media_list_player = None
        self.videopanel = ttk.Frame(self.parent)
        self.canvas = Tk.Canvas(self.videopanel).pack(fill=Tk.BOTH,expand=1)
        self.videopanel.pack(fill=Tk.BOTH,expand=1)
        ctrlpanel = ttk.Frame(self.parent)
        pause  = ttk.Button(ctrlpanel, text="Pause", command=self.OnPause)
        play   = ttk.Button(ctrlpanel, text="Play", command=self.OnPlay)
        stop   = ttk.Button(ctrlpanel, text="Stop", command=self.OnStop)
        next   = ttk.Button(ctrlpanel, text="Next", command=self.OnSkip)
        volume = ttk.Button(ctrlpanel, text="Volume", command=self.OnSetVolume)
        pause.pack(side=Tk.LEFT)
        play.pack(side=Tk.LEFT)
        stop.pack(side=Tk.LEFT)
        next.pack(side=Tk.LEFT)
        volume.pack(side=Tk.LEFT)
        self.volume_var = Tk.IntVar()
        self.volslider = Tk.Scale(ctrlpanel, variable=self.volume_var, command=self.volume_sel,
                from_=0, to=100, orient=Tk.HORIZONTAL, length=100)
        self.volslider.pack(side=Tk.LEFT)
        ctrlpanel.pack(side=Tk.BOTTOM)
        ctrlpanel2 = ttk.Frame(self.parent)
        self.scale_var = Tk.DoubleVar()
        self.timeslider_last_val = ""
        self.timeslider = Tk.Scale(ctrlpanel2, variable=self.scale_var, command=self.scale_sel,
                from_=0, to=1000, orient=Tk.HORIZONTAL, length=500)
        self.timeslider.pack(side=Tk.BOTTOM, fill=Tk.X,expand=1)
        self.timeslider_last_update = time.time()
        ctrlpanel2.pack(side=Tk.BOTTOM,fill=Tk.X)
        self.media_list = vlc.MediaList()
        self.timer = ttkTimer(self.OnTimer, 1.0)
        self.timer.start()
        self.parent.update()

    def OnExit(self, evt):
        self.Close()

    def OnOpen(self):
        if os.path.isfile("sch.txt"):
            pass
            print("found sch.txt")
            print("playing from this file instead")
        else:
            print("sch.txt not found")
            fullname =  askdirectory(initialdir = "/",title = "Select Directory")
            if os.path.isdir(fullname):
                video_frmt = ['.mp4', '.m4a', '.m4v', '.f4v', '.f4a', '.m4b', '.m4r', '.f4b', '.mov', '.wmv', '.wma', '.asf', '.webm', '.flv', '.avi', '.wav', '.mkv']
                mastr = []
                hold = []
                mastrw = []
                for dir in os.listdir(fullname):
                    dirpath = os.path.join(fullname, dir).replace("\\","/")
                    for path, directories, files in os.walk(dirpath):
                        for filename in files:
                            name, ext = os.path.splitext(filename)
                            if ext in video_frmt:
                                hold.append(os.path.join(path, filename).replace("\\","/"))
                            else:
                                pass
                    if len(hold):
                        mastr.append(hold)
                    else:
                        pass
                    hold = []
                while mastr:
                    randitem = choice(mastr)
                    if len(randitem):
                        mastrw.append(randitem.pop(0))
                    else:
                        mastr.remove(randitem)
                with open('sch.txt', 'w') as f:
                    for fullpath in mastrw:
                        f.write(fullpath+'\n')
                print("created sch.txt")
        with open("sch.txt") as flplpay:
            sch_list = flplpay.read().split('\n')
            for path_line in sch_list:
                self.media = vlc.Media(path_line)
                self.media_list.add_media(self.media)
        self.media_list_player = vlc.MediaListPlayer()
        self.media_list_player.set_media_list(self.media_list)
        print("Created MediaListPlayer")
        if platform.system() == 'Windows':
            self.media_list_player.get_media_player().set_hwnd(self.GetHandle())
        else:
            self.media_list_player.get_media_player().set_xwindow(self.GetHandle())
        self.OnPlay()
        self.volslider.set(self.media_list_player.get_media_player().audio_get_volume())

    def OnPlay(self):
        if not self.media_list_player.get_media_player():
            self.OnOpen()
            print("no media playing")
        else:
            print("now playing {}")
            # title = self.media_list_player.get_media_player().get_title()
            # self.SetTitle(title)
            if self.media_list_player.play() == -1:
                self.errorDialog("Unable to play.")

    def GetHandle(self):
        return self.videopanel.winfo_id()

    def OnPause(self):
        self.media_list_player.pause()
        print("Paused")

    def OnStop(self):
        self.media_list_player.stop()
        self.timeslider.set(0)
        print("Stopped")

    def OnSkip(self):
        self.media_list_player.next()
        print("Skipping {}")

    def OnTimer(self):
        if self.media_list_player == None:
            return
        length = self.media_list_player.get_media_player().get_length()
        dbl = length * 0.001
        self.timeslider.config(to=dbl)
        tyme = self.media_list_player.get_media_player().get_time()
        if tyme == -1:
            tyme = 0
        dbl = tyme * 0.001
        if time.time() > (self.timeslider_last_update + 2.0):
            self.timeslider.set(dbl)

    def scale_sel(self, evt):
        if self.media_list_player == None:
            return
        nval = self.scale_var.get()
        sval = str(nval)
        if self.timeslider_last_val != sval:
            self.timeslider_last_update = time.time()
            mval = "%.0f" % (nval * 1000)
            self.media_list_player.get_media_player().set_time(int(mval))

    def volume_sel(self, evt):
        if self.media_list_player == None:
            return
        volume = self.volume_var.get()
        if volume > 100:
            volume = 100
        if self.media_list_player.get_media_player().audio_set_volume(volume) == -1:
            self.errorDialog("Failed to set volume")

    def OnToggleVolume(self, evt):
        is_mute = self.media_list_player.get_media_player().audio_get_mute()
        self.media_list_player.get_media_player().audio_set_mute(not is_mute)
        self.volume_var.set(self.media_list_player.get_media_player().audio_get_volume())

    def OnSetVolume(self):
        volume = self.volume_var.get()
        if volume > 100:
            volume = 100
        if self.media_list_player.get_media_player().audio_set_volume(volume) == -1:
            self.errorDialog("Failed to set volume")

    def errorDialog(self, errormessage):
        Tk.tkMessageBox.showerror(self, 'Error', errormessage)

def Tk_get_root():
    if not hasattr(Tk_get_root, "root"):
        Tk_get_root.root= Tk.Tk()
    return Tk_get_root.root

def SetTitle(self):
    root.title(title.get())

def _quit():
    print("user quit")
    root = Tk_get_root()
    root.quit()
    root.destroy()
    os._exit(1)

if __name__ == "__main__":
    root = Tk_get_root()
    root.protocol("WM_DELETE_WINDOW", _quit)
    media_list_player = Player(root, title="Python-VLC PLayer")
    root.wm_attributes("-topmost", 1)
    root.mainloop()

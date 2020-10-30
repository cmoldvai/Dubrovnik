import sys
from tkinter import *
from dubLibs import boardcom
from dubLibs import dubrovnik as du

# class Checkbar(Frame):
#     def __init__(self, parent=None, picks=[], side=LEFT, anchor=W):
#         Frame.__init__(self, parent)
#         self.vars = []
#         for pick in picks:
#             var = IntVar()
#             chk = Checkbutton(self, text=pick, variable=var)
#             chk.pack(side=side, anchor=anchor, expand=YES)
#             self.vars.append(var)
#     def state(self):
#         return [var.get() for var in self.vars]


class Radiobar(Frame):
    def __init__(self, parent=None, picks=[], side=LEFT, anchor=W):
        Frame.__init__(self, parent)
        self.var = StringVar()
        self.var.set(picks[0])  # selects the first entry
        for pick in picks:
            rad = Radiobutton(self, text=pick, value=pick, variable=self.var)
            rad.pack(side=side, anchor=anchor, expand=YES)

    def state(self):
        return self.var.get()


if __name__ == '__main__':

    def blockErase():
        blockSize = var.get()
        du.block_erase(comm, block_size=blockSize,
                       start_addr="00", trig=False, echo=1)

    def exitApp():
        # del comm
        sys.exit()

    # Connecting to the board
    defaultPort = 5
    comm = boardcom.detect_ports(defaultPort)

    root = Tk()

    # lng = Checkbar(root, ['Python', 'C#', 'Java', 'C++'])
    gui = Radiobar(root, ['4kB', '32kB', '64kB', 'All'], side=TOP, anchor=NW)
    # tgl = Checkbar(root, ['All'])

    gui.pack(side=LEFT, fill=Y)
    # lng.pack(side=TOP,  fill=X)
    # tgl.pack(side=LEFT)
    # lng.config(relief=GROOVE, bd=2)
    gui.config(relief=RIDGE,  bd=2)

    def allstates():
        # print(gui.state(), lng.state(), tgl.state())
        print(gui.state())

    # from quitter import Quitter
    # Quitter(root).pack(side=RIGHT)
    Button(root, text='Quit', command=exitApp).pack(side=RIGHT)
    Button(root, text='Erase', command=blockErase).pack(side=RIGHT)
    root.mainloop()

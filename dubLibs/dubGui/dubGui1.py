import sys
from tkinter import *
from dubLibs import boardcom
from dubLibs import dubrovnik as du

def onErase():
    rb_val = rb_var.get()
    print(rb_val)

# Connecting to the board
defaultPort = 5
comm = boardcom.detect_ports(defaultPort)

root = Tk()
root.title('root = Tk()')

win1 = Frame(root).pack(side=LEFT,fill=Y)
win2 = Frame(root).pack(side=RIGHT)
win3 = Frame(root).pack(side=RIGHT)

Label(win1, text='Block Erase Size').pack(side=TOP,anchor=NW)
# creating the radio buttons for selecting block erase size
rb_var = StringVar()
memsize = ['4','32','64','Chip']
rb1 = Radiobutton(win1, text=memsize[0], variable=rb_var, value=memsize[0])
rb2 = Radiobutton(win1, text=memsize[1], variable=rb_var, value=memsize[1])
rb3 = Radiobutton(win1, text=memsize[2], variable=rb_var, value=memsize[2])
rb4 = Radiobutton(win1, text=memsize[3], variable=rb_var, value=memsize[3])

rb1.pack(side=TOP,anchor=NW)
rb2.pack(side=TOP,anchor=NW)
rb3.pack(side=TOP,anchor=NW)
rb4.pack(side=TOP,anchor=NW)
rb_var.set(memsize[2])

# btn1 = Button(win1, text='Win1').pack(fill=X,side=TOP)
# btn_erase = Button(win2, text='Erase',command=onErase).pack(fill=X, side=TOP,anchor=NE)
# btn_quit = Button(win3, text='Quit',command=sys.exit).pack(fill=X, side=TOP,anchor=SE)
btn_erase = Button(win2, text='Erase',command=onErase).pack(side=RIGHT)
btn_quit = Button(win3, text='Quit',command=sys.exit).pack(side=RIGHT)

root.mainloop()

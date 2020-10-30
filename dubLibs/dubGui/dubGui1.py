from tkinter import *
root = Tk()
root.title('root = Tk()')

win1 = Frame(root).pack(side=LEFT,fill=Y)
win2 = Frame(root).pack(side=RIGHT)
win3 = Frame(root).pack(side=RIGHT)

var = StringVar()
memsize = ['4','32','64','All']
Label(win1, text='Size [kB]')
rb1 = Radiobutton(win1, text='4kB', variable=var, value=memsize[0]).pack(side=TOP,anchor=NW)
rb2 = Radiobutton(win1, text='32kB', variable=var, value=memsize[1]).pack(side=TOP,anchor=NW)
rb3 = Radiobutton(win1, text='64kB', variable=var, value=memsize[2]).pack(side=TOP,anchor=NW)
rb4 = Radiobutton(win1, text='Chip', variable=var, value=memsize[3]).pack(side=TOP,anchor=NW)
var.set(memsize[2])

# btn1 = Button(win1, text='Win1').pack(fill=X,side=TOP)
btn2 = Button(win2, text='Erase').pack(fill=X, side=TOP,anchor=NE)
btn3 = Button(win3, text='Quit').pack(fill=X, side=TOP,anchor=SE)

root.mainloop()

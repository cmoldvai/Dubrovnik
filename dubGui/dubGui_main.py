'''
This is the Flash Operations main program.
It imports modules for Erasing, Programming a flash device.
The program is written in very concise fashion.
The app window is built up by importing individual frames for
Program, Erase and other operations. The import is done in a loop.
'''
import sys
from tkinter import *
from dubLibs import boardcom
from dubLibs import dubrovnik as du
import dubGui_Erase
import dubGui_Program
import dubGui_Connection

# list of filenames (strings) containing individual frames for Program, Erase,...
# TODO
# Change this into a dictionary:
# key: module name
# value: class name (so not all classes should be called flashOps)
# Example:
# frameDict = {'dubGui_Connection':'Connection',
#             'dubGui_Erase':'Erase',
#             'dubGui_Program':'Program'}
#
# for key,value in frameDict.items():
#     print(key + ' : ' + value)
#
# frameList = ['dubGui_Erase', 'dubGui_Program', 'dubGui_Connection']
# parts = []

# builds the main window by importing individual frames for Program, Erase,...
# def buildWindow(root):
#     for frame in frameList:
#         module = __import__(frame)
#         part = module.flashOps(root)
#         # part.config(bd=2, relief=GROOVE)
#         part.config(bd=2, relief=FLAT)
#         part.pack(side=TOP, fill=BOTH)
#         parts.append(part)


def buildWindow(root):
    global part0
    part0 = dubGui_Connection.Connection(root)
    part1 = dubGui_Erase.Erase(root)
    part2 = dubGui_Program.Program(root)

    part0.config(bd=2, relief=GROOVE)
    part1.config(bd=2, relief=GROOVE)
    part2.config(bd=2, relief=GROOVE)

    part0.pack(side=TOP, fill=BOTH)
    part1.pack(side=TOP, fill=BOTH)
    part2.pack(side=TOP, fill=BOTH)

    print(part0)

def dumpState():
    print('print stuff')

root = Tk()
root.title('Flash Operations')
# comm = boardcom.Comm()
buildWindow(root)  # this is where the app window is built

status_bar = Label(root, text='Status bar')
status_bar.config(bd=1, relief=SUNKEN)
status_bar.pack(side=BOTTOM, fill=X, anchor=NW, padx=10, pady=10)

main_btn = Button(root, text='States', command=dumpState)
main_btn.pack(side=BOTTOM, padx=10, pady=5)

comm = boardcom.Comm()
portList = boardcom.Comm().findPorts()
part0.combo.set(portList[0])
part0.comm = comm
dubGui_Program.comm = comm
dubGui_Erase.com = comm



# portList = part0.findPorts()
# # portList = comm.findPorts()
# port = portList[0]

# connectedPort = comm.connect(port)


root.mainloop()

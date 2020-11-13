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

# list of filenames (strings) containing individual frames for Program, Erase,...
# TODO
# Change this into a dictionary:
# key: module name
# value: class name (so not all classes should be called flashOps)
# Example:
# frameDict = {'dubGui_Erase':'flashOps',
#             'dubGui_Program':'flashOps',
#             'dubGui_Connection':'connectFrame'}

# for key,value in frameDict.items():
#     print(key + ' : ' + value)

frameList = ['dubGui_Erase', 'dubGui_Program']
parts = []

# builds the main window by importing individual frames for Program, Erase,...
def buildWindow(root):
    for frame in frameList:
        module = __import__(frame)
        part = module.flashOps(root)
        part.config(bd=2, relief=GROOVE)
        part.pack(side=TOP, fill=BOTH)
        parts.append(part)


def dumpState():
    print('print stuff')


root = Tk()
root.title('Flash Operations')
buildWindow(root)                     # this is where the app window is built
Label(root, text='Placeholder Label').pack(side=TOP)
Button(root, text='States', command=dumpState).pack(side=TOP, fill=X)
root.mainloop()

'''
This is the Flash Operations main program.
It imports modules for Erasing, Programming a flash device.
The program is written in very concise fashion.
The app window is built up by importing individual frames for
Program, Erase and other operations. The import is done in a loop.
'''
import sys
import json
from tkinter import *
from dubLibs import boardcom
from dubLibs import dubrovnik as du
import dubGui_Erase
import dubGui_Program
import dubGui_Connection


def saveState():
    D = {'autoConnect': str(serCom.chk_var.get()),
         'blkEraseSize': str(erase.blockSize.get()),
         'eraseNumBlocks': str(erase.numBlocks.get()),
         'comPort': 'COM5',
         'selPort': 1
         }
    print(D)
    f = open('dubrovnik.json', 'w')
    json.dump(D, f)
    f.close()


root = Tk()
root.title('Flash Operations')

comm = boardcom.BoardComm()
portList = comm.findPorts()

serCom = dubGui_Connection.SerComInterface(root)  # invoking the class
serCom.config(bd=2, relief=GROOVE)
serCom.pack(side=TOP, fill=BOTH)
serCom.combo.set(portList[0])
serCom.comm = comm

erase = dubGui_Erase.Erase(root)  # invoking the class
erase.config(bd=2, relief=GROOVE)
erase.pack(side=TOP, fill=BOTH)
erase.comm = comm     # initializeing self.com in Erase class

program = dubGui_Program.Program(root)  # invoking the class
program.config(bd=2, relief=GROOVE)
program.pack(side=TOP, fill=BOTH)
program.comm = comm   # initializeing self.com in Program class

status_bar = Label(root, text='Status bar')
status_bar.config(bd=1, relief=SUNKEN)
status_bar.pack(side=BOTTOM, fill=X, anchor=NW, padx=10, pady=10)

main_btn = Button(root, text='Save States', command=saveState)
main_btn.pack(side=BOTTOM, padx=10, pady=5)

if serCom.autoConnect:
    serCom.connectPort()

root.mainloop()

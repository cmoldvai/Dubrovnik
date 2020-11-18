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
import dubGui.dubGui_Erase as ers
import dubGui.dubGui_Program as prg 
import dubGui.dubGui_Connection as con

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
root.title('Dubrovnik TestBench')

comm = boardcom.BoardComm()
portList = comm.findPorts()

serCom = con.SerCom(root, DEBUG=True)  # invoking the class
serCom.config(bd=2, relief=GROOVE)
serCom.pack(side=TOP, fill=BOTH)
serCom.combo.set(portList[0])
serCom.comm = comm

erase = ers.Erase(root, DEBUG=True)  # invoking the class
erase.config(bd=2, relief=GROOVE)
erase.pack(side=TOP, fill=BOTH)
erase.comm = comm     # initializeing self.com in Erase class

program = prg.Program(root)  # invoking the class
program.config(bd=2, relief=GROOVE)
program.pack(side=TOP, fill=BOTH)
program.comm = comm   # initializeing self.com in Program class

status_bar = Label(root, text='Status bar')
status_bar.config(bd=1, relief=SUNKEN)
status_bar.pack(side=BOTTOM, fill=X, anchor=W, padx=10, pady=10)

def updtStsBar(statusMsg):
    print(statusMsg)
    status_bar.config(text=statusMsg)

main_btn = Button(root, text='Save States', command=saveState)
main_btn.pack(side=BOTTOM, padx=10, pady=5)

test_btn = Button(root, text='Test Button', command= lambda:updtStsBar('status msg'))
test_btn.pack(side=BOTTOM, pady=10)

if serCom.autoConnect:
    serCom.connectPort()

root.mainloop()

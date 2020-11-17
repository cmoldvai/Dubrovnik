import sys
from tkinter import *
from dubLibs import boardcom
from dubLibs import dubrovnik as du


class Program(Frame):

    startAddr = 0
    dataLen = 0
    endAddr = 0
    pattn = 'cafe0000'
    incr = '1'
    global comm

    def __init__(self, parent=None):
        LabelFrame.__init__(self, parent, text='Program', padx=5, pady=5)
        self.pack(side=TOP, anchor=NW, padx=10, pady=10)
        self.start_addr = StringVar()
        self.length = StringVar()
        self.pattern = StringVar()
        self.increment = StringVar()
        self.buildFrame()

    def buildFrame(self):
        '''Makes a reusable frame for a flash program operation'''
        lbl1 = Label(self, text='Pattern: 0x').grid(
            row=1, column=0, padx=5, pady=5, sticky=E)
        ent1 = Entry(self, textvariable=self.pattern).grid(row=1, column=1)
        self.pattern.set('caba0000')

        lbl2 = Label(self, text='Increment: 0x').grid(
            row=2, column=0, padx=5, pady=5, sticky=E)
        ent2 = Entry(self, textvariable=self.increment).grid(row=2, column=1)
        self.increment.set('1')

        lbl3 = Label(self, text='Start Address: 0x').grid(
            row=3, column=0, padx=5, pady=5, sticky=E)
        ent3 = Entry(self, textvariable=self.start_addr).grid(row=3, column=1)
        self.start_addr.set('60')

        lbl4 = Label(self, text='Length: 0x').grid(
            row=4, column=0, padx=5, pady=5, sticky=E)
        ent4 = Entry(self, textvariable=self.length).grid(row=4, column=1)
        self.length.set('250')

        btn2 = Button(self, text='Message', command=self.message).grid(
            row=5, column=0, padx=10, pady=10)

        btn3 = Button(self, text='Program', command=self.program).grid(
            row=5, column=1, padx=10, pady=10)

        btn4 = Button(self, text='Quit', command=sys.exit).grid(
            row=5, column=2, padx=10, pady=10)

    def get_states(self):
        global startAddr
        global dataLen
        global endAddr
        global pattn
        global incr
        startAddr = int(self.start_addr.get(), 16)
        dataLen = int(self.length.get(), 16)
        endAddr = startAddr + dataLen
        pattn = self.pattern.get()
        incr = self.increment.get()

    def program(self):
        self.get_states()
        print('startAddr: %x, dataLen: %x, pattn: %s, incr: %s' %
              (startAddr, dataLen, pattn, incr))
        du.pattern_program(comm, startAddr, dataLen, pattn, incr)
        print('programming done.')

    def message(self):
        self.get_states()
        print(f'Start address = {startAddr:8X}')
        print(f'Length        = {dataLen:8X}')
        print(f'End address   = {endAddr:8X}')
        print(f'Pattern       = {pattn}')
        print(f'Increment     = {incr}')


if __name__ == "__main__":

    comm = boardcom.Comm()   # create an instance of class Comm
    portList = comm.findPorts()
    port = portList[0]
    connectedPort = comm.connect(port)

    # Program().mainloop()
    i_prog = Program()  # create and instance of class Program() (debug only: not needed)

    mainloop()

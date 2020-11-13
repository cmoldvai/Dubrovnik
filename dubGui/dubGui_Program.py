import sys
from tkinter import *
from dubLibs import boardcom
from dubLibs import dubrovnik as du


class flashOps(Frame):

    startAddr = 0
    dataLen = 0
    endAddr = 0
    pattn = 'cafe0000'
    incr = '1'

    def __init__(self, parent=None):
        Frame.__init__(self, parent)  # do a superclass init
        self.pack()
        self.start_addr = StringVar()
        self.length = StringVar()
        self.pattern = StringVar()
        self.increment = StringVar()
        self.makeframe_program()

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
        print(f'Pattern       = {pattn:8X}')
        print(f'Increment     = {incr:8X}')

    def makeframe_program(self):
        '''Makes a reusable frame for a flash program operation'''
        Label(self, text='Program').grid(row=0, column=0, sticky=W)

        lbl1 = Label(self, text='Pattern: 0x').grid(
            row=1, column=0, padx=5, pady=5)
        ent1 = Entry(self, textvariable=self.pattern).grid(row=1, column=1)
        self.pattern.set('caba0000')

        lbl2 = Label(self, text='Increment: 0x').grid(
            row=2, column=0, padx=5, pady=5)
        ent2 = Entry(self, textvariable=self.increment).grid(row=2, column=1)
        self.increment.set('1')

        lbl3 = Label(self, text='Start Address: 0x').grid(
            row=3, column=0, padx=5, pady=5)
        ent3 = Entry(self, textvariable=self.start_addr).grid(row=3, column=1)
        self.start_addr.set('60')

        lbl4 = Label(self, text='Length: 0x').grid(
            row=4, column=0, padx=5, pady=5)
        ent4 = Entry(self, textvariable=self.length).grid(row=4, column=1)
        self.length.set('250')

        btn2 = Button(self, text='Message', command=self.message).grid(
            row=5, column=0, padx=10, pady=10)

        btn3 = Button(self, text='Program', command=self.program).grid(
            row=5, column=1, padx=10, pady=10)

        btn4 = Button(self, text='Quit', command=sys.exit).grid(
            row=5, column=2, padx=10, pady=10)


if __name__ == "__main__":

    # Connecting to the board
    # defaultPort = 5
    # comm = boardcom.findport_autoconnect(defaultPort)

    portList = boardcom.find_ports()
    defaultPort = portList[0]
    comm = boardcom.connect2port(defaultPort)

    flashOps().mainloop()

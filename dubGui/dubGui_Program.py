from tkinter import *
from dubLibs import dubrovnik as du


class Program(Frame):

    startAddr = 0
    dataLen = 0
    endAddr = 0
    pattn = 'cafe0000'
    incr = '1'

    def __init__(self, parent=None, DEBUG=False):
        LabelFrame.__init__(self, parent, text='Program', padx=5, pady=5)
        self.pack(side=TOP, anchor=NW, padx=10, pady=10)
        self.DEBUG = DEBUG
        self.start_addr = StringVar()
        self.length = StringVar()
        self.pattern = StringVar()
        self.increment = StringVar()
        self.progMode = IntVar()
        self.progModes = ['patter','file']
        self.comm = None
        self.buildFrame()
        self.progMode.set(self.progModes[0])

    def buildFrame(self):
        '''Makes a reusable frame for a flash program operation'''
        rb_file = Radiobutton(self, text='Use Pattern', variable=self.progMode, value=self.progModes[0])
        rb_file.grid(row=1, column=0, padx=10, pady=2, sticky=W)

        rb_pattn = Radiobutton(self, text='Load from File', variable=self.progMode, value=self.progModes[1])
        rb_pattn.grid(row=2, column=0, padx=10, pady=2, sticky=W)

        pat_lbl = Label(self, text='Pattern: 0x').grid(
            row=0, column=1, padx=5, pady=5, sticky=E)
        pat_ent = Entry(self, textvariable=self.pattern).grid(row=0, column=2)
        self.pattern.set('caba0000')
        
        incr_lbl = Label(self, text='Increment: 0x').grid(
            row=1, column=1, padx=5, pady=5, sticky=E)
        incr_ent = Entry(self, textvariable=self.increment).grid(row=1, column=2)
        self.increment.set('1')

        sa_lbl = Label(self, text='Start Address: 0x').grid(
            row=2, column=1, padx=5, pady=5, sticky=E)
        sa_ent = Entry(self, textvariable=self.start_addr).grid(row=2, column=2)
        self.start_addr.set('60')

        len_lbl = Label(self, text='Length: 0x').grid(
            row=3, column=1, padx=5, pady=5, sticky=E)
        len_ent = Entry(self, textvariable=self.length).grid(row=3, column=2)
        self.length.set('250')

        prog_btn = Button(self, text='Program', width=10, command=self.program).grid(
            row=5, column=1, padx=10, pady=10)

        if self.DEBUG:
            msg_btn = Button(self, text='Message', width=10, command=self.message).grid(
            row=5, column=0, padx=10, pady=10)
            
            quit_btn = Button(self, text='Quit', width=10, command=sys.exit)
            quit_btn.grid(row=5, column=2, padx=10, pady=10)

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
        du.pattern_program(self.comm, startAddr, dataLen, pattn, incr)
        print('programming done.')

    def message(self):
        self.get_states()
        print(f'Start address = {startAddr:8X}')
        print(f'Length        = {dataLen:8X}')
        print(f'End address   = {endAddr:8X}')
        print(f'Pattern       = {pattn}')
        print(f'Increment     = {incr}')


if __name__ == "__main__":

    from dubLibs import boardcom

    comm = boardcom.BoardComm()   # create an instance of class Comm
    portList = comm.findPorts()
    port = portList[0]
    connectedPort = comm.connect(port)

    # Program().comm = comm  # assign to self.comm in Program class
    Program(DEBUG=True).comm = comm

    mainloop()

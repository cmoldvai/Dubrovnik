import os
import pickle
import json
from tkinter import *
from tkinter import ttk
from dubLibs import boardcom
from dubLibs import dubrovnik as du
from tkinter.filedialog import askopenfilename


class SerCom(Frame):
    def __init__(self, parent=None, DEBUG=False):
        LabelFrame.__init__(
            self, parent, text='Serial Connection', padx=10, pady=10)
        self.pack(side=TOP, anchor=NW, padx=10, pady=10)
        self.DEBUG = DEBUG
        self.STANDALONE = False
        self.comm = None                      # object created by boardcom
        self.portStatus = 'disconnected'
        self.selPort = ''  # ! keeps track of selected port, between calls
        self.portList = []
        self.portHandle = None
        self.chk_var = IntVar()
        self.autoConnect = 0
        self.buildFrame()

    def buildFrame(self):
        '''Makes a reusable frame for a connecting to Dubrovnik board'''
        chk = Checkbutton(self, text='Auto connect', variable=self.chk_var)
        chk.grid(row=0, column=0)

        self.combo = ttk.Combobox(
            self, width=10, values=self.portList, postcommand=self.updtPortList)
        self.combo.grid(row=0, column=1, padx=10)

        self.btn2 = Button(self, text='Connect', width=10,
                           command=self.connectPort)
        self.btn2.grid(row=0, column=2, padx=10)

        if self.STANDALONE:
            self.btn3 = Button(self, text='Save Config', width=10,
                               command=self.saveConfig)
            self.btn3.grid(row=0, column=3, padx=10, sticky=E)

        if self.DEBUG:
            self.test_btn = Button(self, text='Testing',
                                   width=10, command=self.testSerComm)
            self.test_btn.grid(row=1, column=0, padx=5, pady=10, columnspan=1)
            self.test_lbl = Label(
                self, text="Debug message:", anchor=W, justify='left')
            self.test_lbl.grid(row=1, column=1, padx=5,
                               pady=10, sticky=EW, columnspan=3)

    def updtPortList(self):
        self.portList = self.comm.findPorts()
        self.combo['values'] = self.portList
        self.combo.set(portList[0])

    def connectPort(self, defaultPort=None):
        if self.portStatus == 'disconnected':
            if defaultPort:
                self.selPort = defaultPort         # updates class variable as well
            else:
                self.selPort = self.combo.get()
            # if disconnected, then connect to selected port
            self.portHandle = self.comm.connect(
                self.selPort)
            self.combo.set(self.selPort)
            self.setSerialParams()
            self.btn2.config(text='Disconnect')  # change button label
            # self.btn2['text'] = 'Disconnect'
            self.portStatus = 'connected'  # update connection status
            serParams = f'Connected: {self.comPort} ({self.comBaudrate},{self.comBytesize},{self.comParity},{self.comStopbits},{self.comXonXoff})'
            stsBarComm.config(text=serParams)

        elif self.portStatus == 'connected':
            # if connected, then disconnect from the port connected to
            self.disconnectPort(self.selPort)
            self.btn2['text'] = 'Connect'  # update button label
            self.portStatus = 'disconnected'  # update connection status
            stsBarComm.config(text='Disconnected')
        else:
            print('No such port. Try again!!!')

    def disconnectPort(self, selPort):
        self.comm.disconnect(selPort)
        print("Port: %s disconnected" % selPort)
        stsBarComm.config(text='No COM port found!')

    def testSerComm(self):
        serParams = '%s, baud=%d, bytes=%1d,\nparity=%s, stop=%1d, protocol=%s' \
            % (self.comPort, self.comBaudrate, self.comBytesize, self.comParity, self.comStopbits, self.comXonXoff)
        self.test_lbl.config(text=serParams)
        stsBarComm.config(text=serParams)

    def setSerialParams(self):
        """ Gets serial communication port parameters """
        self.comPort = self.portHandle.port
        self.comBaudrate = self.portHandle.baudrate
        self.comBytesize = self.portHandle.bytesize
        self.comParity = self.portHandle.parity
        self.comStopbits = self.portHandle.stopbits
        self.comXonXoff = self.portHandle.xonxoff

    def saveConfig(self):
        if self.STANDALONE:
            cfg = {'autoConnect': serCom.chk_var.get(),
                   'lastUsedPort': serCom.selPort,
                   'blkEraseSize': str(erase.blockSize.get()),
                   'eraseNumBlocks': str(erase.numBlocks.get()),
                   'pattern': program.pattern.get(),
                   'increment': program.increment.get(),
                   'start_addr': program.start_addr.get(),
                   'length': program.length.get()
                   }
            print(cfg)
            f = open('test.json', 'w')
            json.dump(cfg, f)
            f.close()
        else:
            pass


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
        self.progModes = ['pattern', 'file']
        self.comm = None
        self.buildFrame()
        self.progMode.set(self.progModes[0])

    def buildFrame(self):
        '''Makes a reusable frame for a flash program operation'''
        rb_file = Radiobutton(self, text='Use Pattern',
                              variable=self.progMode, value=self.progModes[0])
        rb_file.grid(row=1, column=0, padx=10, pady=2, sticky=W)

        rb_pattn = Radiobutton(self, text='Load from File',
                               variable=self.progMode, value=self.progModes[1])
        rb_pattn.grid(row=2, column=0, padx=10, pady=2, sticky=W)

        pat_lbl = Label(self, text='Pattern: 0x').grid(
            row=0, column=1, padx=5, pady=5, sticky=E)
        pat_ent = Entry(self, textvariable=self.pattern).grid(row=0, column=2)
        self.pattern.set('caba0000')

        incr_lbl = Label(self, text='Increment: 0x').grid(
            row=1, column=1, padx=5, pady=5, sticky=E)
        incr_ent = Entry(self, textvariable=self.increment).grid(
            row=1, column=2)
        self.increment.set('1')

        sa_lbl = Label(self, text='Start Address: 0x').grid(
            row=2, column=1, padx=5, pady=5, sticky=E)
        sa_ent = Entry(self, textvariable=self.start_addr).grid(
            row=2, column=2)
        self.start_addr.set('60')

        len_lbl = Label(self, text='Length: 0x').grid(
            row=3, column=1, padx=5, pady=5, sticky=E)
        len_ent = Entry(self, textvariable=self.length).grid(row=3, column=2)
        self.length.set('250')

        prog_btn = Button(self, text='Program', width=10, command=self.program).grid(
            row=5, column=1, padx=10, pady=10)

        open_btn = Button(self, text='Open', width=10, command=self.openFile).grid(
            row=5, column=0, padx=10, pady=10)

        if self.DEBUG:
            test_btn = Button(self, text='Quit', width=10, command=sys.exit)
            # test_btn = Button(self, text='Quit', width=10, command=self.message)
            test_btn.grid(row=5, column=2, padx=10, pady=10)

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

    def openFile(self):
        filename = askopenfilename(title='Select File to Program', initialdir=os.getcwd(
        ), filetypes=(('All files', '*.*'), ('Binary files', '*.bin'), ('Hex files', '*.hex')))
        print(filename)
        f = open(filename, 'r')
        print(f.read())
        f.close()

    def message(self):
        self.get_states()
        print(f'Start address = {startAddr:8X}')
        print(f'Length        = {dataLen:8X}')
        print(f'End address   = {endAddr:8X}')
        print(f'Pattern       = {pattn}')
        print(f'Increment     = {incr}')


class Erase(Frame):
    def __init__(self, parent=None, DEBUG=False):
        LabelFrame.__init__(self, parent, text='Erase',
                            relief=GROOVE, padx=10, pady=10)
        self.pack(side=TOP, anchor=NW, padx=10, pady=10)
        self.DEBUG = DEBUG
        self.comm = None
        self.pageSize = 0x100
        self.blockSize = StringVar()
        self.startAddr = StringVar()
        self.numBlocks = StringVar()
        self.blockSizes = ['4', '32', '64', 'Chip']
        self.buildFrame()
        self.blockSize.set(self.blockSizes[0])

    def buildFrame(self, parent=None):
        '''Makes a reusable frame for a flash erase operation'''
        # ersfrm = LabelFrame(self, parent).pack(side=LEFT, anchor=NW, padx=10,pady=10)
        rb1 = Radiobutton(self, text='4kB',
                          variable=self.blockSize, value=self.blockSizes[0])
        rb1.grid(row=0, column=0, padx=10, pady=2)
        rb2 = Radiobutton(self, text='32kB',
                          variable=self.blockSize, value=self.blockSizes[1])
        rb2.grid(row=1, column=0, padx=10, pady=2)
        rb3 = Radiobutton(self, text='64kB',
                          variable=self.blockSize, value=self.blockSizes[2])
        rb3.grid(row=2, column=0, padx=10, pady=2)
        rb4 = Radiobutton(self, text='Chip',
                          variable=self.blockSize, value=self.blockSizes[3])
        rb4.grid(row=3, column=0, padx=10, pady=2)

        lbl = Label(self, text='Start Address:  0x')
        lbl.grid(row=0, column=1, padx=10, pady=2, sticky=E)
        ent1 = Entry(self, textvariable=self.startAddr)
        ent1.grid(row=0, column=2, sticky=W)

        self.startAddr.set('0')

        lbl2 = Label(self, text='Num. Blocks:  0x')
        lbl2.grid(row=1, column=1, padx=10, pady=2, sticky=E)
        ent2 = Entry(self, textvariable=self.numBlocks)
        ent2.grid(row=1, column=2, sticky=W)

        self.numBlocks.set('3')

        btn2 = Button(self, text='Erase', width=12,
                      justify='center', command=self.blockErase)
        btn2.grid(row=3, column=2, padx=2, pady=2)

        if self.DEBUG:
            lbl4 = Label(self, text='Results here:')
            lbl4.grid(row=4, column=0, sticky=E)

            quit_btn = Button(self, text='Quit', width=12, command=sys.exit)
            quit_btn.grid(row=3, column=1, padx=2, pady=2)

    def blockErase(self):
        blkSzStr = self.blockSize.get()

        if blkSzStr == 'Chip':
            print('Erasing entire chip')
            self.comm.send('6; 60; wait 0')
            print(self.comm.response())
            print('Chip erase done.')
        else:
            # must be in else, otherwise it fails for 'Chip'
            block_size = int(blkSzStr) # don't change it to hex int(blkSzStr, 16). Will fail
            start_addr = int(self.startAddr.get(), 16)
            # # Calculating the actual start addresses:
            # mask = ~((block_size * 1024) - 1)  #! Tricky. Pay attention:
            # actStartAddr = start_addr & mask
            print(f'Start address = {start_addr:x}')
            # print(f'Actual start address = {actStartAddr:x}')
            numm_blocks = int(self.numBlocks.get(), 16)
            print(f'Erasing {numm_blocks} {block_size}kB block(s)')
            du.block_erase(self.comm, block_size=block_size,
                           start_addr=start_addr, num_blocks=numm_blocks)
            print('Block erase done.')

        print('Elapsed time: {}ms')

    def message(self):
        self.data += 1
        print('Hello from world %s!' % self.data)


if __name__ == "__main__":

    def updtStsBar(statusMsg):
        print(statusMsg)
        stsBarComm.config(text=statusMsg)

    def loadConfig():
        fname = 'dubrovnik.cfg'
        try:
            fname = open(fname, 'r')
            cfg = json.load(fname)
            print(cfg)
            # get autoConnect from the file ...
            serCom.autoConnect = cfg['autoConnect']
            # ... set checkbox accordingly
            serCom.chk_var.set(serCom.autoConnect)
            serCom.selPort = cfg['lastUsedPort']     # get last used port
            serCom.lastUsedPort = serCom.selPort     # ... and set it
            erase.blockSize.set(cfg['blkEraseSize'])
            erase.numBlocks.set(cfg['eraseNumBlocks'])
            program.pattern.set(cfg['pattern'])
            program.increment.set(cfg['increment'])
            program.start_addr.set(cfg['start_addr'])
            program.length.set(cfg['length'])
            fname.close()
        except FileNotFoundError:
            loadDefaultSettings()
            

    def loadDefaultSettings():
            serCom.chk_var.set(0)
            serCom.selPort = ''
            # serCom.lastUsedPort = ''
            erase.blockSize.set('4')
            erase.numBlocks.set('3')
            program.pattern.set('caba0000')
            program.increment.set('1')
            program.start_addr.set('20')
            program.length.set('40')

    def saveConfig():
        cfg = {'autoConnect': serCom.chk_var.get(),
               'lastUsedPort': serCom.selPort,
               'blkEraseSize': str(erase.blockSize.get()),
               'eraseNumBlocks': str(erase.numBlocks.get()),
               'pattern': program.pattern.get(),
               'increment': program.increment.get(),
               'start_addr': program.start_addr.get(),
               'length': program.length.get()
               }
        print(cfg)
        f = open('dubrovnik.cfg', 'w')
        json.dump(cfg, f, indent=3)
        f.close()

    root = Tk()

    comm = boardcom.BoardComm()   # create an instance of class Comm
    portList = comm.findPorts()

    serCom = SerCom(root, DEBUG=False)  # invoking the class
    serCom.config(bd=2, relief=GROOVE)
    serCom.pack(side=TOP, fill=BOTH)
    serCom.combo.set(portList[0])
    serCom.comm = comm

    program = Program(root, DEBUG=False)  # invoking the class
    program.config(bd=2, relief=GROOVE)
    program.pack(side=TOP, fill=BOTH)
    program.comm = comm   # initializeing self.com in Program class

    erase = Erase(root, DEBUG=False)  # invoking the class
    erase.config(bd=2, relief=GROOVE)
    erase.pack(side=TOP, fill=BOTH)
    erase.comm = comm     # initializeing self.com in Erase class

    stsBarComm = Label(root, text='Not connected', font=(
        "Helvetica", 8), anchor=W, justify=LEFT, pady=2)
    stsBarComm.config(bd=1, relief=SUNKEN)
    stsBarComm.pack(side=BOTTOM, fill=X, anchor=W, padx=10, pady=10)

    test_btn1 = Button(root, text='Save Config',
                       command=saveConfig)
    test_btn1.pack(side=BOTTOM, pady=10)

    test_btn2 = Button(root, text='Load Config',
                       command=loadConfig)
    test_btn2.pack(side=BOTTOM, pady=10)

    # test_btn3 = Button(root, text='Default Config',
    #                    command=loadDefaultSettings)
    # test_btn3.pack(side=BOTTOM, pady=10)

    # ############ MENU
    my_menu = Menu(root)
    root.config(menu=my_menu)

    file_menu = Menu(my_menu, tearoff=False)
    my_menu.add_cascade(label="File", menu=file_menu)
    file_menu.add_command(label="New")
    file_menu.add_command(label="Open")
    file_menu.add_command(label="Save")
    file_menu.add_command(label="Save As")
    file_menu.add_separator()
    file_menu.add_command(label="Exit")

    config_menu = Menu(my_menu, tearoff=False)
    my_menu.add_cascade(label="Config", menu=config_menu)
    config_menu.add_command(label="Load config",command=loadConfig)
    config_menu.add_command(label="Store config",command=saveConfig)
    config_menu.add_command(label="Default config",command=loadDefaultSettings)
    # config_menu.add_separator()
    # config_menu.add_command(label="Exit")

    tools_menu = Menu(my_menu, tearoff=False)
    my_menu.add_cascade(label="Tools", menu=tools_menu)
    tools_menu.add_command(label="Open script",command=loadConfig)
    tools_menu.add_command(label="Distribution",command=loadConfig)
    tools_menu.add_command(label="Other tools",command=saveConfig)

    help_menu = Menu(my_menu, tearoff=False)
    my_menu.add_cascade(label="Help", menu=help_menu)
    help_menu.add_command(label="Help")
    help_menu.add_separator()
    help_menu.add_command(label="About")



    loadConfig()

    if serCom.autoConnect:  # if autoConnect set
        if len(portList) > 1:  # no need to check for 0. boardcom.py already does
            # if last used port is on the list (is available)
            if serCom.lastUsedPort in portList:
                serCom.connectPort(serCom.lastUsedPort)  # connect to that port
        else:
            # serCom.connectPort()  # if only 1 port, of lastUsedPort not on the list
            # if only 1 port, of lastUsedPort not on the list
            serCom.connectPort(portList[0])
    # if no autoConnect, just fall through

    mainloop()

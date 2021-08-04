import os
import sys
# import pickle
import json
from tkinter import *
from tkinter import ttk
from dubLibs import boardcom
from dubLibs import dubrovnik as du
from tkinter.filedialog import askopenfilename
from tkinter.messagebox import askretrycancel, showerror


class SerCom(Frame):
    def __init__(self, parent=None, DEBUG=False):
        LabelFrame.__init__(
            self, parent, text='Serial Connection',
            width=200, height=500, padx=10, pady=10)
        # self.pack(side=TOP, anchor=NW, padx=10, pady=10)
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

    def checkConnection(self):
        if self.portStatus == 'disconnected':
            showerror('No Connection!', 'Connect to the board')

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
                   }
            print(cfg)
            f = open('connection.cfg', 'w')
            json.dump(cfg, f)
            f.close()
        else:
            pass

    def testSerComm(self):
        serParams = '%s, baud=%d, bytes=%1d,\nparity=%s, stop=%1d, protocol=%s' \
            % (self.comPort, self.comBaudrate, self.comBytesize, self.comParity, self.comStopbits, self.comXonXoff)
        self.test_lbl.config(text=serParams)


class Program(Frame):
    startAddr = 0
    dataLen = 0
    endAddr = 0
    pattn = 'cafe0000'
    incr = '1'
    progData = []

    def __init__(self, parent=None, DEBUG=False):
        LabelFrame.__init__(self, parent, text='Program', padx=5, pady=5)
        # self.pack(side=TOP, anchor=NW, padx=10, pady=10)
        self.DEBUG = DEBUG
        self.start_addr = StringVar()
        self.length = StringVar()
        self.pattern = StringVar()
        self.increment = StringVar()
        self.progModeVar = StringVar()
        self.progModeList = ['pattern', 'file']
        self.comm = None
        self.buildFrame()  # buld and draw the frame
        # set up the inital values in the frame
        self.progModeVar.set(self.progModeList[0])

    def buildFrame(self):
        '''Makes a reusable frame for a flash program operation'''
        rb_file = Radiobutton(self, text='Use Pattern', variable=self.progModeVar,
                              value=self.progModeList[0], command=self.grayOutEntry)
        rb_file.grid(row=1, column=0, padx=10, pady=2, sticky=W)

        rb_pattn = Radiobutton(self, text='Load from File', variable=self.progModeVar,
                               value=self.progModeList[1], command=self.grayOutEntry)
        rb_pattn.grid(row=2, column=0, padx=10, pady=2, sticky=W)

        lbl1_prog = Label(self, text='Pattern: 0x')
        lbl1_prog.grid(row=0, column=1, padx=5, pady=5, sticky=E)
        self.ent1_prog = Entry(self, textvariable=self.pattern)
        self.ent1_prog.grid(row=0, column=2)
        self.pattern.set('caba0000')

        lbl2_prog = Label(self, text='Increment: 0x')
        lbl2_prog.grid(row=1, column=1, padx=5, pady=5, sticky=E)
        self.ent2_prog = Entry(self, textvariable=self.increment)
        self.ent2_prog.grid(row=1, column=2)
        self.increment.set('1')

        lbl3_prog = Label(self, text='Start Address: 0x')
        lbl3_prog.grid(row=2, column=1, padx=5, pady=5, sticky=E)
        self.ent3_prog = Entry(self, textvariable=self.start_addr)
        self.ent3_prog.grid(row=2, column=2)
        self.start_addr.set('60')

        lbl4_prog = Label(self, text='Length: 0x')
        lbl4_prog.grid(row=3, column=1, padx=5, pady=5, sticky=E)
        self.ent4_prog = Entry(self, textvariable=self.length)
        self.ent4_prog.grid(row=3, column=2)
        self.length.set('250')

        self.btn_openFile = Button(self, text='Open', width=10, command=self.openFile, state=DISABLED)
        self.btn_openFile.grid(row=5, column=0, padx=10, pady=10)
        self.btn_progFile = Button(self, text='Program', width=10, command=self.program)
        self.btn_progFile.grid(row=5, column=2, padx=10, pady=10)

        if self.DEBUG:
            test_btn = Button(self, text='Program test',
                              width=10, command=self.program_test)
            # test_btn = Button(self, text='TestMsg', width=10, command=self.message)
            test_btn.grid(row=5, column=0, padx=10, pady=10)

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

    def grayOutEntry(self):
        if self.progModeVar.get() == 'file':
            self.ent1_prog.config(state=DISABLED)
            self.ent2_prog.config(state=DISABLED)
            self.ent4_prog.config(state=DISABLED)
            self.btn_openFile.config(state=NORMAL)
        else:
            self.ent1_prog.config(state=NORMAL)
            self.ent2_prog.config(state=NORMAL)
            self.ent4_prog.config(state=NORMAL)
            self.btn_openFile.config(state=DISABLED)

    def program(self):
        serCom.checkConnection()  # check if board is connected
        self.get_states()
        if self.progModeVar.get() == 'pattern':
            print('startAddr: %x, dataLen: %x, pattn: %s, incr: %s' %
                  (startAddr, dataLen, pattn, incr))
            endAddr = startAddr + dataLen
            du.pattern_program(self.comm, startAddr, endAddr, pattn, incr)
            print('programming done.')
        else:   # if programming a content of a file
            dsize = len(self.progData)
            du.write_buf_write(comm, self.progData, dsize)
            du.data_program(comm, self.progData, startAddr)
            pass


    def openFile(self):
        filename = askopenfilename(title='Select File to Program', initialdir=os.getcwd(
        ), filetypes=(('All files', '*.*'), ('Binary files', '*.bin'), ('Hex files', '*.hex')))
        print(filename)
        fnameParts = os.path.splitext(filename)
        extension = fnameParts[-1]
        if extension.lower() == '.bin':
            with open(filename, 'rb') as f:
                # self.progData = bytes(f.read(), 'utf-8')
                self.progData = f.read()
                print(self.progData)

    def program_test(self):
        self.get_states()
        print(f'Pattern       = {self.pattern.get()}')
        print(f'Increment     = {self.increment.get()}')
        print(f'Start address = {self.start_addr.get()}')
        print(f'End address   = {self.length.get()}')
        print('\n')


class Erase(Frame):
    def __init__(self, parent=None, DEBUG=False):
        LabelFrame.__init__(self, parent, text='Erase',
                            relief=GROOVE, padx=10, pady=10)
        # self.pack(side=TOP, anchor=NW, padx=10, pady=10)
        self.grid()
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
        rb1_ers = Radiobutton(self, text='4kB',
                              variable=self.blockSize, value=self.blockSizes[0])
        rb1_ers.grid(row=0, column=0, padx=10, pady=2, sticky=W)
        rb2_ers = Radiobutton(self, text='32kB',
                              variable=self.blockSize, value=self.blockSizes[1])
        rb2_ers.grid(row=1, column=0, padx=10, pady=2, sticky=W)
        rb3_ers = Radiobutton(self, text='64kB',
                              variable=self.blockSize, value=self.blockSizes[2])
        rb3_ers.grid(row=2, column=0, padx=10, pady=2, sticky=W)
        rb4_ers = Radiobutton(self, text='Chip',
                              variable=self.blockSize, value=self.blockSizes[3])
        rb4_ers.grid(row=3, column=0, padx=10, pady=2, sticky=W)

        lbl_ers = Label(self, text='Start Address:  0x')
        lbl_ers.grid(row=0, column=1, padx=10, pady=2, sticky=E)
        ent1_ers = Entry(self, textvariable=self.startAddr)
        ent1_ers.grid(row=0, column=2, sticky=W)

        self.startAddr.set('0')

        lbl2_ers = Label(self, text='Num. Blocks:  0x')
        lbl2_ers.grid(row=1, column=1, padx=10, pady=2, sticky=E)
        ent2_ers = Entry(self, textvariable=self.numBlocks)
        ent2_ers.grid(row=1, column=2, sticky=W)

        self.numBlocks.set('3')

        btn2_ers = Button(self, text='Erase', width=12,
                          justify='center', command=self.blockErase)
        btn2_ers.grid(row=3, column=2, padx=2, pady=2)

        if self.DEBUG:
            lbl4_ers = Label(self, text='Results here:')
            lbl4_ers.grid(row=4, column=0, sticky=E)

            quit_btn_ers = Button(self, text='Erase test',
                                  width=12, command=self.erase_test)
            quit_btn_ers.grid(row=3, column=1, padx=2, pady=2)

    def blockErase(self):
        serCom.checkConnection()  # check if board is connected
        blkSzStr = self.blockSize.get()
        if blkSzStr == 'Chip':
            print('Erasing entire chip')
            self.comm.send('6; 60; wait 0')
            print(self.comm.response())
            print('Chip erase done.')
        else:
            # must be in else, otherwise it fails for 'Chip'
            # don't change it to hex int(blkSzStr, 16). Will fail
            block_size = int(blkSzStr)
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

    def erase_test(self):
        print(f'Selected Erase Block Size : {self.blockSize.get()}')
        print(f'Start Address             : {self.startAddr.get()}')
        print(f'Number of Blocks          : {self.numBlocks.get()}')
        print('\n')


class Read(Frame):
    def __init__(self, parent=None, DEBUG=False):
        LabelFrame.__init__(self, parent, text='Read',
                            relief=GROOVE, padx=10, pady=10)
        # self.pack(side=TOP, anchor=NW, padx=10, pady=10)
        self.DEBUG = DEBUG
        self.comm = None
        self.spiMode = StringVar()
        self.startAddr = StringVar()
        self.readLength = StringVar()
        self.spiModes = ['SPI', 'Dual',
                         'Quad (114)', 'Quad (144)', 'QPI (444)', 'Octal']
        self.buildFrame()
        self.spiMode.set(self.spiModes[0])

    def buildFrame(self, parent=None):
        '''Makes a reusable frame for a flash erase operation'''
        # ersfrm = LabelFrame(self, parent).pack(side=LEFT, anchor=NW, padx=10,pady=10)
        rb1_read = Radiobutton(self, text=self.spiModes[0],
                               variable=self.spiMode, value=self.spiModes[0])
        rb1_read.grid(row=0, column=0, padx=10, pady=2, sticky=W)
        rb2_read = Radiobutton(self, text=self.spiModes[1],
                               variable=self.spiMode, value=self.spiModes[1])
        rb2_read.grid(row=1, column=0, padx=10, pady=2, sticky=W)
        rb3_read = Radiobutton(self, text=self.spiModes[2],
                               variable=self.spiMode, value=self.spiModes[2])
        rb3_read.grid(row=2, column=0, padx=10, pady=2, sticky=W)
        rb4_read = Radiobutton(self, text=self.spiModes[3],
                               variable=self.spiMode, value=self.spiModes[3])
        rb4_read.grid(row=3, column=0, padx=10, pady=2, sticky=W)
        rb5_read = Radiobutton(self, text=self.spiModes[4],
                               variable=self.spiMode, value=self.spiModes[4])
        rb5_read.grid(row=4, column=0, padx=10, pady=2, sticky=W)
        rb6_read = Radiobutton(self, text=self.spiModes[5],
                               variable=self.spiMode, value=self.spiModes[5])
        rb6_read.grid(row=5, column=0, padx=10, pady=2, sticky=W)

        lbl_read = Label(self, text='Start Address:  0x')
        lbl_read.grid(row=0, column=1, padx=10, pady=2, sticky=E)
        ent1_read = Entry(self, textvariable=self.startAddr)
        ent1_read.grid(row=0, column=2, sticky=W)

        self.startAddr.set('0')
        self.readLength.set('200')

        lbl2_read = Label(self, text='Lenght:  0x')
        lbl2_read.grid(row=1, column=1, padx=10, pady=2, sticky=E)
        ent2_read = Entry(self, textvariable=self.readLength)
        ent2_read.grid(row=1, column=2, sticky=W)

        # self.spiMode.set('0')

        btn1_read = Button(self, text='Read', width=12,
                           justify='center', command=self.readFlash)
        btn1_read.grid(row=5, column=2, padx=2, pady=2)

        if self.DEBUG:
            btn2_read = Button(self, text='Read test',
                               width=12, command=self.readFlash)
            btn2_read.grid(row=5, column=1, padx=2, pady=2)

    def readFlash(self):
        serCom.checkConnection()  # check if board is connected
        readStartAddr = int(self.startAddr.get(), 16)
        readLen = int(self.readLength.get(), 16)
        print(f'SPI Mode      : {self.spiMode.get()}')
        print(f'Start Address : {readStartAddr}')
        print(f'Read Lenght   : {readLen}')
        du.read(comm, staddr=readStartAddr, length=readLen, echo=1)


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
            erase.blockSize.set(cfg['eraseBlkSize'])
            erase.startAddr.set(cfg['eraseStartAddr'])
            erase.numBlocks.set(cfg['eraseNumBlocks'])
            program.pattern.set(cfg['progPattern'])
            program.increment.set(cfg['progIncrement'])
            program.start_addr.set(cfg['progStartAddr'])
            program.length.set(cfg['progLength'])
            read.spiMode.set(cfg['readSpiMode'])
            read.startAddr.set(cfg['readStartAddr'])
            read.readLength.set(cfg['readLength'])
            fname.close()
        except FileNotFoundError:
            loadDefaultSettings()
            saveConfig()

    def loadDefaultSettings():
        serCom.chk_var.set(0)
        serCom.selPort = ''
        # serCom.lastUsedPort = ''
        erase.blockSize.set(erase.blockSizes[0])
        erase.startAddr.set('0')
        erase.numBlocks.set('1')
        program.pattern.set('cafe0000')
        program.increment.set('1')
        program.start_addr.set('0')
        program.length.set('100')
        read.spiMode.set(read.spiModes[0])
        read.startAddr.set('0')
        read.readLength.set('100')

    def saveConfig():
        cfg = {'autoConnect': serCom.chk_var.get(),
               'lastUsedPort': serCom.selPort,
               'eraseBlkSize': str(erase.blockSize.get()),
               'eraseStartAddr': str(erase.startAddr.get()),
               'eraseNumBlocks': str(erase.numBlocks.get()),
               'progPattern': program.pattern.get(),
               'progIncrement': program.increment.get(),
               'progStartAddr': program.start_addr.get(),
               'progLength': program.length.get(),
               'readSpiMode': read.spiMode.get(),
               'readStartAddr': read.startAddr.get(),
               'readLength': read.readLength.get()
               }
        print(cfg)
        f = open('dubrovnik.cfg', 'w')
        json.dump(cfg, f, indent=3)
        f.close()

    root = Tk()
    root.title('Dubrovnik Communication App')

    comm = boardcom.BoardComm()   # create an instance of class Comm
    portList = comm.findPorts()

    serCom = SerCom(root, DEBUG=False)  # invoking the class
    # serCom.pack(side=TOP, fill=BOTH)
    serCom.grid_propagate(0)
    serCom.config(width=350, height=100, bd=2, relief=GROOVE)
    serCom.grid(row=0, column=0, padx=10, pady=10, sticky=NW)
    serCom.combo.set(portList[0])
    serCom.comm = comm

    erase = Erase(root, DEBUG=False)  # invoking the class
    # erase.pack(side=LEFT, fill=BOTH)
    erase.grid_propagate(0)
    erase.config(width=350, height=210, bd=2, relief=GROOVE)
    erase.grid(row=1, column=0, padx=10, pady=10, sticky=NW)
    erase.comm = comm     # initializeing self.com in Erase class

    program = Program(root, DEBUG=False)  # invoking the class
    # program.pack(side=LEFT, fill=BOTH)
    program.grid_propagate(0)
    program.config(width=380, height=210, bd=2, relief=GROOVE)
    program.grid(row=1, column=1, padx=10, pady=10, sticky=NW)
    program.comm = comm   # initializeing self.com in Program class

    read = Read(root, DEBUG=False)  # invoking the class
    # read.pack(side=LEFT, fill=BOTH)
    read.grid_propagate(0)
    read.config(width=380, height=210, bd=2, relief=GROOVE)
    read.grid(row=1, column=2, padx=10, pady=10, sticky=NW)
    read.comm = comm     # initializeing self.com in Erase class

    stsBarComm = Label(root, text='Not connected', font=(
        "Helvetica", 9), anchor=W, justify=LEFT, pady=2)
    stsBarComm.config(bd=1, relief=SUNKEN)
    # stsBarComm.pack(side=BOTTOM, fill=X, anchor=W, padx=10, pady=10)
    # stsBarComm.grid_propagate(0)
    stsBarComm.grid(row=3, column=0, padx=10, pady=10, columnspan=3, sticky=EW)

    # test_btn1 = Button(root, text='Save Config',
    #                    command=saveConfig)
    # test_btn1.pack(side=BOTTOM, pady=10)

    # test_btn2 = Button(root, text='Load Config',
    #                    command=loadConfig)
    # test_btn2.pack(side=BOTTOM, pady=10)

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

    tools_menu = Menu(my_menu, tearoff=False)
    my_menu.add_cascade(label="Tools", menu=tools_menu)
    tools_menu.add_command(label="Open script", command=loadConfig)
    tools_menu.add_command(label="Distribution", command=loadConfig)
    tools_menu.add_command(label="Other tools", command=saveConfig)

    config_menu = Menu(my_menu, tearoff=False)
    my_menu.add_cascade(label="Config", menu=config_menu)
    config_menu.add_command(label="Load config", command=loadConfig)
    config_menu.add_command(label="Store config", command=saveConfig)
    config_menu.add_command(label="Restore defaults",
                            command=loadDefaultSettings)

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

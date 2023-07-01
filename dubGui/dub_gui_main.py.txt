# from dubGui.serialTerminalShell import Terminal
import os
import sys
import json
import time
from tkinter import *
from tkinter import ttk
from tkinter import scrolledtext
from dubLibs import boardcom
from dubLibs import dubrovnik  # instead of "from dubLibs import Dubrovnik as du"
from tkinter.filedialog import askopenfilename
from tkinter.messagebox import showerror, showwarning, showinfo

PROMPT = '>>> '
CLEAR_CMD = 'clear'


class SerComFrame(Frame):
    def __init__(self, parent=None, DEBUG=False):
        LabelFrame.__init__(self, parent, text='Serial Connection',
                            padx=10, pady=10)
        self.DEBUG = DEBUG
        self.STANDALONE = False
        self.comm = None                      # object created by boardcom
        self.portStatus = 'disconnected'
        self.selPort = ''  # ! keeps track of the selected port, between calls
        self.portList = []
        self.portHandle = None
        self.chk_var = IntVar()
        self.autoConnect = 0
        self.serParams = ''

        # Check if %AppData%\Dubrovnik folder exists. If not create one
        appData = os.getenv('APPDATA')  # get location of %AppData% in Windows
        if appData[-1] == '\\':
            appData = appData[:-1]  # get rid of the trailing backslash, if any
        # append 'Dubrovnik' folder
        # create folder name string
        self.dubrovnikConfigPath = f'{appData}\\Dubrovnik'
        if not os.path.isdir(self.dubrovnikConfigPath):  # if folder doesn't exist
            # print(self.dubrovnikConfigPath)
            os.mkdir(self.dubrovnikConfigPath)  # ...make one

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

    def connectPort(self, defaultPort=None, checkIsFlashPresent=True):
        if self.portStatus == 'disconnected':
            if defaultPort:
                self.selPort = defaultPort         # updates class variable as well
                self.combo.set(self.selPort)
            else:
                self.selPort = self.combo.get()
            # only if disconnected, connect to selected port
            self.portHandle = self.comm.connect(self.selPort)
            self.setSerialParams()
            self.btn2.config(text='Disconnect')  # change button label
            self.portStatus = 'connected'  # update connection status
            self.serParams = f'Connected: {self.comPort} ({self.comBaudrate},{self.comBytesize},{self.comParity},{self.comStopbits},{self.comXonXoff})'
            if checkIsFlashPresent:  # allow this part to run only when enabled by func argument
                if comm.isFlashPresent():
                    pn = du.get_part_number(comm)
                    serCom.serParams += '    Device: ' + pn
            stsBarComm.config(text=self.serParams)

        elif self.portStatus == 'connected':
            # if connected, disconnect from the current port
            self.disconnectPort(self.selPort)
            self.btn2['text'] = 'Connect'  # update button label
            self.portStatus = 'disconnected'  # update connection status
            stsBarComm.config(text='Disconnected')
        else:
            print('No such port. Try again!!!')
        self.saveConfig()

    def disconnectPort(self, selPort):
        self.comm.disconnect(selPort)
        # print(f"Port: {selPort} disconnected")
        stsBarComm.config(text='No COM port found!')

    def checkConnection(self):
        if self.portStatus == 'disconnected':
            showerror('Dubrovnik Dashboard Error',
                      'Unable to open COM port!\nConnect to the board')

    def setSerialParams(self):
        """ Gets serial communication port parameters """
        self.comPort = self.portHandle.port
        self.comBaudrate = self.portHandle.baudrate
        self.comBytesize = self.portHandle.bytesize
        self.comParity = self.portHandle.parity
        self.comStopbits = self.portHandle.stopbits
        self.comXonXoff = self.portHandle.xonxoff

    def loadDefaultSettings(self):
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

    def saveConfig(self):
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
        with open(f'{self.dubrovnikConfigPath}\dubrovnik.cfg', 'w') as fh:
            # print(cfg)  # TODO remove print when stable
            json.dump(cfg, fh, indent=3)

    def loadConfig(self):
        fname = f'{self.dubrovnikConfigPath}\dubrovnik.cfg'
        try:
            fname = open(fname, 'r')
            cfg = json.load(fname)  # get configuration from .cfg file
            serCom.autoConnect = cfg['autoConnect']  # get autoConnect config
            serCom.chk_var.set(serCom.autoConnect)   # ...set checkbox
            serCom.selPort = cfg['lastUsedPort']     # get last used port
            serCom.lastUsedPort = serCom.selPort     # ...set it
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
            self.loadDefaultSettings()
            self.saveConfig()

    def testSerComm(self):
        serParams = '%s, baud=%d, bytes=%1d,\nparity=%s, stop=%1d, protocol=%s' \
            % (self.comPort, self.comBaudrate, self.comBytesize, self.comParity, self.comStopbits, self.comXonXoff)
        self.test_lbl.config(text=serParams)


class ProgramFrame(Frame):
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
        self.buildFrame()
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

        self.btn_openFile = Button(
            self, text='Open', width=10, command=self.openFile, state=DISABLED)
        self.btn_openFile.grid(row=5, column=0, padx=10, pady=10)
        self.btn_progFile = Button(
            self, text='Program', width=10, command=self.program)
        self.btn_progFile.grid(row=5, column=1, padx=10, pady=10)
        self.btn_progVer = Button(self, text='Prog/Verify',
                                  width=10, command=self.progVerify, state=DISABLED)
        self.btn_progVer.grid(row=5, column=2, padx=10, pady=10)

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
            print(
                f'startAddr: {startAddr:X}, dataLen: {dataLen:x}, pattn: {pattn}, incr: {incr}')
            print('Programming...')
            t_prog = du.page_program(
                self.comm, startAddr, dataLen, pattn, incr)
            term.tprint(du.textToDisplay[:-1])
            # term.displayText(du.textToDisplay)
        else:   # if programming a content of a file
            term.displayText('Downloading data...\n')
            dsize = len(self.progData)
            du.write_buf_write(comm, self.progData, dsize)
            term.displayText('Programming...\n')
            # term.tprint('Programming...\n')
            t_prog = du.data_program(comm, self.progData, startAddr)
            term.tprint(du.textToDisplay[:-1])
        prog_time = du.time_conv_from_usec(t_prog)
        print(f'DONE. Effective programming time: {prog_time}')

    def progVerify(self):
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
                # print(self.progData)


class EraseFrame(Frame):
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

        lbl2_ers = Label(self, text='Num. Blocks:    ')
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
        blkSzStr = self.blockSize.get().lower()
        start_addr = int(self.startAddr.get(), 16)
        num_blocks = int(self.numBlocks.get())

        if blkSzStr != 'chip':  # if it is a '4','32' or '64
            block_size = int(blkSzStr)
            blockSizeKB = block_size * 1024
            startAddr = (start_addr // blockSizeKB) * blockSizeKB
            term.tprint(f'Erasing {num_blocks} {block_size}kB block(s) from address {startAddr:x}',
                        printOn='guiConsole')
            t_erase = du.block_erase(
                self.comm, block_size, start_addr, num_blocks)
        else:
            term.tprint('Erasing chip', printOn='guiConsole')
            t_erase = du.block_erase(self.comm, blkSzStr)

        term.tprint(du.textToDisplay[:-1])
        erase_time = du.time_conv_from_usec(t_erase)
        print(f'DONE. Elapsed time: {erase_time}')

    def erase_test(self):
        print(f'Selected Erase Block Size : {self.blockSize.get()}')
        print(f'Start Address             : {self.startAddr.get()}')
        print(f'Number of Blocks          : {self.numBlocks.get()}')
        print('\n')


class ReadFrame(Frame):
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

        dispmode_lbl = Label(self, text='Display Mode: ')
        dispmode_lbl.grid(row=4, column=1, padx=5, sticky="E")

        # add "HexView (h)": 'h'}
        self.dispmodeOptions = {"Binary (b)": 'b', "DWord (w)": 'w'}
        options = list(self.dispmodeOptions.keys())
        self.dispmode_cb = ttk.Combobox(
            self, width=16, values=options)
        self.dispmode_cb.grid(row=4, column=2, padx=5, sticky="E")

        self.dispmode_cb.set(options[0])
        du.dispmode = self.dispmodeOptions[options[0]]

        self.dispmode_cb.bind('<<ComboboxSelected>>', self.dispmode_cb_updated)

        btn1_read = Button(self, text='Read', width=12,
                           justify='center', command=self.readFlash)
        btn1_read.grid(row=5, column=2, padx=2, pady=2)

        if self.DEBUG:
            btn2_read = Button(self, text='Read test',
                               width=12, command=self.readFlash)
            btn2_read.grid(row=5, column=1, padx=2, pady=2)

    def dispmode_cb_updated(self, event):
        dispModeSelKey = self.dispmode_cb.get()  # get the selected item in Combo
        # assign the associated value to dispmode
        mode = self.dispmodeOptions[dispModeSelKey]
        du.dispmode = mode  # update dispmode in class Dubrovnik
        self.modeKeys = list(self.dispmodeOptions.keys())
        if mode == 'b':
            self.dispmode_cb.set(self.modeKeys[0])
        elif mode == 'w':
            self.dispmode_cb.set(self.modeKeys[1])
        else:
            # change it to [2] once hexView 'h' is implemented
            self.dispmode_cb.set(self.modeKeys[0])

    def readFlash(self):
        serCom.checkConnection()  # check if board is connected
        readStartAddr = int(self.startAddr.get(), 16)
        readLen = int(self.readLength.get(), 16)
        # print(f'SPI Mode      : {self.spiMode.get()}')
        # print(f'Start Address : {readStartAddr}')
        # print(f'Read Lenght   : {readLen}')
        du.read(comm, start_addr=readStartAddr, length=readLen, echo=0)
        term.tprint(du.textToDisplay[:-1], printOn='guiConsole')


class Terminal(Frame):
    def __init__(self, parent=None):
        LabelFrame.__init__(self, parent, text='Terminal',
                            relief=GROOVE, padx=10, pady=10)
        self.comm = None
        self.history = []
        self.historyIndex = 0
        # CM TODO: check if needed. displayText implemented differently
        self.textToDisplay = None

        # clear_btn = Button(self, text="Clear Display", command=self.clear)
        # clear_btn.grid(row=0, column=0, padx=10, sticky='W')

        self.txt = scrolledtext.ScrolledText(
            self, wrap=CHAR, width=80, height=24, font=("Consolas", 11))
        self.txt.grid(row=1, column=0, columnspan=99,
                      pady=10, padx=10, sticky="NSEW")

        self.clear()
        self.txt.focus()      # placing cursor in text area

        # Key bindings
        self.txt.bind('<Return>', self.onReturnKey)
        self.txt.bind('<BackSpace>', self.onBackSpace)
        self.txt.bind('<Delete>', self.onDelete)
        self.txt.bind('<Up>', self.onUpArrowKey)
        self.txt.bind('<Down>', self.onDownArrowKey)
        self.txt.bind('<Left>', self.onLeftArrowKey)

    def displayText(self, text):
        self.txt.insert(END, '\n' + text)
        self.txt.insert(END, '\n' + PROMPT)
        self.txt.mark_set(INSERT, END)
        self.txt.see(INSERT)

    def onReturnKey(self, event):
        cmdstr = self.txt.get("end-1l linestart", "end-1l lineend")[
            len(PROMPT):].strip()
        print(cmdstr)
        if len(cmdstr) > 0:
            self.history.append(cmdstr)

        if cmdstr == CLEAR_CMD:
            self.clear()
            return 'break'
        elif len(cmdstr) > 0:
            try:
                comm.send(cmdstr)
                resp = comm.response(removeCmd=True, removePrompt=True).strip()
            except Exception as e:
                resp = f'error from boardcom: {e}'
            if resp != '':
                self.txt.insert(END, '\n' + resp)

        self.txt.insert(END, '\n' + PROMPT)
        self.txt.mark_set(INSERT, END)
        self.txt.see(INSERT)
        self.historyIndex = len(self.history)
        # Returning 'break' prevents the native behavior, i.e. line break.
        return 'break'

    def onBackSpace(self, event):
        return self.allowDelete(5)

    def onDelete(self, event):
        return self.allowDelete(4)

    def allowDelete(self, charIndex):
        cur = self.txt.index(INSERT)
        charPos = int(cur.split('.')[1])
        if charPos < charIndex:
            return 'break'  # Returning 'break' prevents the native behavior, e.g. Del

    def onUpArrowKey(self, event):
        if self.historyIndex > 0:
            self.historyIndex -= 1
        return self.replaceLineWithHistory()

    def onDownArrowKey(self, event):
        if self.historyIndex < len(self.history):
            self.historyIndex += 1
        return self.replaceLineWithHistory()

    def onLeftArrowKey(self, event):
        return self.allowDelete(5)

    def replaceLineWithHistory(self):
        self.txt.delete('end-1l linestart+' +
                        str(len(PROMPT)) + 'c', 'end-1l lineend')

        newLine = ''
        if self.historyIndex < len(self.history):
            newLine = self.history[self.historyIndex]
        self.txt.insert(END, newLine)
        return 'break'  # Returning 'break' prevents the native behavior, e.g. Up/Down/Return

    def clear(self):
        self.txt.delete(1.0, END)
        self.txt.insert(1.0, PROMPT)

    def tprint(self, text, printOn='guiConsole'):
        """Targeted Print\n
        Prints on the targeted console\n
        Input parameters:\n
        text: the text to be printed
        printOn: the target where to print the messages:
            'sysConsole' prints on system console
            'guiConsole' prints in the GUI text window
            'both' prints in both places (it slows down the system)
        """
        if printOn == 'sysConsole':
            print(text)
        elif printOn == 'guiConsole':
            # term.displayText(text)
            self.displayText(text)
            du.textToDisplay = ""
        else:
            print(text)
            # term.displayText(text)
            self.displayText(text)
            du.textToDisplay = ""

    def callCommand(self):
        pass

# class MainWindow:
#     def __init__(self, parent):  # parent or master are good names
#         frame = Frame(parent)    # want to put in into main window (master)
#         frame.pack()

#         self.printButton = Button(frame, text='Print Message', command=self.printMessage)
#         self.printButton.pack(side=LEFT)

#         self.quitButton = Button(frame, text='Quit', command=frame.quit)
#         self.quitButton.pack(side=LEFT)

#     def printMessage(self):
#         print("Wow! It worked :)")


if __name__ == "__main__":

    # def updtStsBar(statusMsg):
    #     print(statusMsg)
    #     stsBarComm.config(text=statusMsg)

    def showAbout():
        aboutMsg = '''
                   ***************************
                   *** Dubrovnik Workbench ***
                   ***************************

                   Ver 0.5

                   Authors:
                   Csaba Moldvai
                   Eyal Barzilay'''
        showinfo('About', aboutMsg)

    def get_vt_distribution():
        pass

    def dub_func_test():
        pass

    def ina230_calibration():
        pass

    def program_sfdp():
        pass

    root = Tk()
    root.title('Dubrovnik Dashboard App')

    comm = boardcom.BoardComm()   # create an instance of class Comm
    du = dubrovnik.Dubrovnik()

    portList = comm.findPorts()
    comport = portList[0]

    # TODO Eventually migrate to a format where MainWindow is in itw own class
    # window = MainWindow(root)

# *******************************************
# ****** Serial Communications Panel ********
# *******************************************
    serCom = SerComFrame(root, DEBUG=False)  # invoking the class
    # serCom.pack(side=TOP, fill=BOTH)
    serCom.grid_propagate(0)
    serCom.config(width=350, height=60, bd=2, relief=GROOVE)
    serCom.grid(row=0, column=0, padx=10, pady=4, sticky=NW)
    serCom.combo.set(portList[0])
    serCom.comm = comm

# ******************************
# ****** Erase Panel   *********
# ******************************
    erase = EraseFrame(root, DEBUG=False)  # invoking the class
    # erase.pack(side=LEFT, fill=BOTH)
    erase.grid_propagate(0)
    erase.config(width=350, height=210, bd=2, relief=GROOVE)
    erase.grid(row=1, column=0, padx=10, pady=4, sticky=NW)
    erase.comm = comm     # initializeing self.com in Erase class

# ******************************
# ****** Program Panel *********
# ******************************
    # TODO rename program to progFrm
    program = ProgramFrame(root, DEBUG=False)  # invoking the class
    # program.pack(side=LEFT, fill=BOTH)
    program.grid_propagate(0)
    program.config(width=380, height=210, bd=2, relief=GROOVE)
    program.grid(row=1, column=1, padx=10, pady=4, sticky=NW)
    program.comm = comm   # initializeing self.com in Program class

# ***************************
# ****** Read Panel *********
# ***************************
    read = ReadFrame(root, DEBUG=False)  # invoking the class
    # read.pack(side=LEFT, fill=BOTH)
    read.grid_propagate(0)
    read.config(width=380, height=210, bd=2, relief=GROOVE)
    read.grid(row=1, column=2, padx=10, pady=4, sticky=NW)
    read.comm = comm     # initializeing self.com in ReadFrame class

# ***********************************
# ******** Terminal Window **********
# ***********************************
    term = Terminal(root)
    # term.config(width=400, height=300)
    # term.grid_propagate(0)
    term.grid(row=2, column=0, padx=10, pady=4, columnspan=99, sticky=NSEW)
    term.grid_columnconfigure(0, weight=1)
    term.grid_rowconfigure(0, weight=1)
    term.comm = comm     # initializeing self.com in Erase class

# ***************************
# ****** Status Bar *********
# ***************************
    stsBarComm = Label(root, text='Not connected', font=(
        "Helvetica", 9), anchor=W, justify=LEFT, pady=2)
    stsBarComm.config(bd=1, relief=SUNKEN)
    # stsBarComm.pack(side=BOTTOM, fill=X, anchor=W, padx=10, pady=10)
    stsBarComm.grid_propagate(0)
    stsBarComm.grid(row=4, column=0, padx=10, pady=4,
                    columnspan=3, sticky=EW)

    # stsBarRight = Label(root, text='Hello', width=10, font=(
    #     "Helvetica", 9), anchor=W, justify=RIGHT, pady=2)
    # stsBarRight.config(bd=1, relief=SUNKEN)
    # # stsBarComm.pack(side=BOTTOM, fill=X, anchor=W, padx=10, pady=10)
    # stsBarRight.grid_propagate(0)
    # stsBarRight.grid(row=4, column=1, padx=10, pady=4,sticky='EW')

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
    #tools_menu.add_command(label="Open script", command=loadConfig)
    tools_menu.add_command(label="VT distribution",
                           command=get_vt_distribution)
    tools_menu.add_command(
        label="Dubrovnik functional test", command=dub_func_test)
    tools_menu.add_command(label="INA230 calibration",
                           command=ina230_calibration)
    tools_menu.add_command(label="SFDP Program", command=program_sfdp)
    tools_menu.add_command(label="Other tools")

    config_menu = Menu(my_menu, tearoff=False)
    my_menu.add_cascade(label="Config", menu=config_menu)
    config_menu.add_command(label="Load config", command=serCom.loadConfig)
    config_menu.add_command(label="Store config", command=serCom.saveConfig)
    config_menu.add_command(label="Restore defaults",
                            command=serCom.loadDefaultSettings)

    help_menu = Menu(my_menu, tearoff=False)
    my_menu.add_cascade(label="Help", menu=help_menu)
    help_menu.add_command(label="Help")
    help_menu.add_separator()
    help_menu.add_command(label="About", command=showAbout)

    serCom.loadConfig()  # includes autoConnect and lastUsedPort

    # * At this point we have a list of valid COM ports.
    # * Next step is to connect to one of them.
    if serCom.autoConnect:  # if autoConnect set
        if len(portList) > 1:  # no need to check if ==0. boardcom.py already does
            if serCom.lastUsedPort in portList:  # if last used port is in the portList
                # connect to that port
                serCom.connectPort(serCom.lastUsedPort,
                                   checkIsFlashPresent=False)
        else:
            # otherwise connect to the first in the list
            serCom.connectPort(portList[0], checkIsFlashPresent=False)
    # If not autoconnect then do not connect to anything

        # * At this point we are connected to the UART chip on Dubrovnik, but not yet
        # * to the MCU. It may require a manual RESET to boot.
        resp = comm.connectToMCU()
        # print(resp)
        term.clear()

        if comm.isFlashPresent() == 0:
            showwarning(
                'Warning', 'No flash device detected\nInstall a device and RESET the board')

    stsBarComm.config(text=serCom.serParams)

    # print(comm.serialAvailable(comport))

    # def timer():
    #     # seconds = time.strftime("%S")
    #     # print(seconds)
    #     # term.displayText(seconds)

    #     numBytes = comm.serialAvailable()
    #     if numBytes > 0:
    #         resp = comm.response()
    #         term.displayText(resp)

    #     # numBytes = comm.serialAvailable(comport)
    #     # term.displayText(str(numBytes))  # print response into the teminal window
    #     # print(f'numBytes: {numBytes}')
    #     timer_lbl.after(1000, timer)  # regularly call function to implement a timer

    # timer_lbl = Label(root, text='')
    # # timer_lbl.pack() # make it invisible. Used as timer for checking serial port
    # timer()  # must call the function once to start it

    mainloop()

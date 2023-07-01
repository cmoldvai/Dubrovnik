import os
# import sys
# import json
# import time
from tkinter import *
from tkinter import ttk
from dubLibs import boardcom
from dubLibs import dpm_lib
from dubLibs import dubrovnik  # instead of "from dubLibs import Dubrovnik as du"
from tkinter.filedialog import askopenfilename
from tkinter.messagebox import showerror, showwarning, showinfo

SERCOM_DBG = False
MEAS_TAB_DBG = False
CFG_TAB_DBG = False


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
        # append 'DPM' folder
        # create folder name string
        self.dpmConfigPath = f'{appData}\\DPM'
        if not os.path.isdir(self.dpmConfigPath):  # if folder doesn't exist
            # print(self.dubrovnikConfigPath)
            os.mkdir(self.dpmConfigPath)  # ...make one

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

    def saveConfig(self):
        pass
        # cfg = {'autoConnect': serCom.chk_var.get(),
        #        'lastUsedPort': serCom.selPort,
        #        'eraseBlkSize': str(erase.blockSize.get()),
        #        'eraseStartAddr': str(erase.startAddr.get()),
        #        'eraseNumBlocks': str(erase.numBlocks.get()),
        #        'progPattern': program.pattern.get(),
        #        'progIncrement': program.increment.get(),
        #        'progStartAddr': program.start_addr.get(),
        #        'progLength': program.length.get(),
        #        'readSpiMode': read.spiMode.get(),
        #        'readStartAddr': read.startAddr.get(),
        #        'readLength': read.readLength.get()
        #        }
        # with open(f'{self.dpmConfigPath}\dpm.cfg', 'w') as fh:
        #     # print(cfg)  # TODO remove print when stable
        #     json.dump(cfg, fh, indent=3)

    def loadConfig(self):
        pass
        # fname = f'{self.dpmConfigPath}\dpm.cfg'
        # try:
        #     fname = open(fname, 'r')
        #     cfg = json.load(fname)  # get configuration from .cfg file
        #     serCom.autoConnect = cfg['autoConnect']  # get autoConnect config
        #     serCom.chk_var.set(serCom.autoConnect)   # ...set checkbox
        #     serCom.selPort = cfg['lastUsedPort']     # get last used port
        #     serCom.lastUsedPort = serCom.selPort     # ...set it
        #     program.pattern.set(cfg['progPattern'])
        #     program.increment.set(cfg['progIncrement'])
        #     program.start_addr.set(cfg['progStartAddr'])
        #     program.length.set(cfg['progLength'])
        #     read.spiMode.set(cfg['readSpiMode'])
        #     read.startAddr.set(cfg['readStartAddr'])
        #     read.readLength.set(cfg['readLength'])
        #     fname.close()
        # except FileNotFoundError:
        #     self.loadDefaultSettings()
        #     self.saveConfig()

    def testSerComm(self):
        serParams = '%s, baud=%d, bytes=%1d,\nparity=%s, stop=%1d, protocol=%s' \
            % (self.comPort, self.comBaudrate, self.comBytesize, self.comParity, self.comStopbits, self.comXonXoff)
        self.test_lbl.config(text=serParams)


class MeasurementFrame(Frame):

    def __init__(self, parent=None, DEBUG=False):
        # LabelFrame.__init__(self, parent, text='Measurements', padx=5, pady=5)
        LabelFrame.__init__(self, parent, padx=5, pady=5)
        # self.pack(side=TOP, anchor=NW, padx=10, pady=10)
        self.DEBUG = DEBUG
        self.vbus = StringVar()
        self.vshunt = StringVar()
        self.current = StringVar()
        self.power = StringVar()
        self.comm = None
        self.buildFrame()

        self.read_test = 'a'

    def buildFrame(self):
        lbl1_vbus = Label(self, text='Vbus')
        lbl1_vbus.grid(row=0, column=0, padx=5, pady=5, sticky=E)
        self.ent1_vbus = Entry(self, justify=RIGHT, font=(
            'Consolas', 11), textvariable=self.vbus)
        self.ent1_vbus.grid(row=0, column=1)
        self.vbus.set('0')

        lbl2_vsht = Label(self, text='Vshunt')
        lbl2_vsht.grid(row=1, column=0, padx=5, pady=5, sticky=E)
        self.ent2_vshunt = Entry(self, justify=RIGHT, font=(
            'Consolas', 11), textvariable=self.vshunt)
        self.ent2_vshunt.grid(row=1, column=1)
        self.vshunt.set('0')

        Label(self, text='V').grid(row=0, column=2, padx=10, pady=5, sticky=W)
        Label(self, text='V').grid(row=1, column=2, padx=10, pady=5, sticky=W)
        Label(self, text='A').grid(row=2, column=2, padx=10, pady=5, sticky=W)
        Label(self, text='W').grid(row=3, column=2, padx=10, pady=5, sticky=W)

        lbl3_curr = Label(self, text='Current')
        lbl3_curr.grid(row=2, column=0, padx=5, pady=5, sticky=E)
        self.ent3_current = Entry(self, justify=RIGHT, font=(
            'Consolas', 11), textvariable=self.current)
        self.ent3_current.grid(row=2, column=1)
        self.current.set('0')

        lbl4_pwr = Label(self, text='Power')
        lbl4_pwr.grid(row=3, column=0, padx=5, pady=5, sticky=E)
        self.ent4_power = Entry(self, justify=RIGHT, font=(
            'Consolas', 11), textvariable=self.power)
        self.ent4_power.grid(row=3, column=1)
        self.power.set('0')

        self.btn_start_meas = Button(
            self, text='Start', width=10, command=self.openFile)
        self.btn_start_meas.grid(
            row=4, column=1, padx=10, pady=10, sticky=EW)

        if self.DEBUG:
            self.test_btn = Button(self, text='Read test',
                                   width=10, command=self.testReadDevice)
            self.test_btn.grid(row=6, column=0, padx=5, pady=10, columnspan=1)
            self.test_lbl = Label(
                self, text="Debug message:", anchor=W, justify='left')
            self.test_lbl.grid(row=6, column=1, padx=5,
                               pady=10, sticky=EW, columnspan=3)

    def testReadDevice(self):
        print('Read Test')
        self.comm.send('rr 0')
        resp = self.comm.response()
        testParams = self.get_states()
        testParams.append(resp)
        self.test_lbl.config(text=testParams)

    def get_states(self):
        global vbus
        global vshunt
        global current
        global power
        # global comm
        vbus = float(self.vbus.get())
        vshunt = float(self.vshunt.get())
        # endAddr = startAddr + dataLen
        current = self.current.get()
        power = self.power.get()
        print(vbus, vshunt, current, power)
        return [vbus, vshunt, current, power]

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

    def singleMeas(self):
        pass
        # serCom.checkConnection()  # check if board is connected
        # self.get_states()
        # if self.progModeVar.get() == 'pattern':
        #     print(
        #         f'startAddr: {startAddr:X}, dataLen: {dataLen:x}, pattn: {pattn}, incr: {incr}')
        #     print('Programming...')
        #     t_prog = du.page_program(
        #         self.comm, startAddr, dataLen, pattn, incr)

        # else:   # if programming a content of a file
        #     dsize = len(self.progData)
        #     du.write_buf_write(comm, self.progData, dsize)
        #     t_prog = du.data_program(comm, self.progData, startAddr)
        # prog_time = du.time_conv_from_usec(t_prog)
        # print(f'DONE. Effective programming time: {prog_time}')

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


class ConfigFrame(Frame):

    def __init__(self, parent=None, DEBUG=False):
        LabelFrame.__init__(self, parent, text='Configuration', padx=5, pady=5)
        # self.pack(side=TOP, anchor=NW, padx=10, pady=10)
        self.DEBUG = DEBUG
        self.vbus = StringVar()
        self.vshunt = StringVar()
        self.current = StringVar()
        self.power = StringVar()
        self.comm = None
        self.chk_var = IntVar()
        self.buildFrame()

    def buildFrame(self):

        adc_conv_time = ['72us', '132us', '258us', '508us', '1.01ms',
                         '2.01ms', '4.01ms', '8.01ms', '16.01ms', '32.01ms', '64.01ms']

        bus_vrange = ['16V', '32V', '60V']

        sh_vrange = ['40mV', '80mV', '160mV', '320mV']

        adc_conv_mode = ['something', 'trig vbus',
                         'trig vshunt', 'cont vbus', 'cont vshunt', 'etc']

        lbl01 = Label(self, text='Conv. Time')
        lbl01.grid(row=0, column=1, padx=5, pady=5, sticky=EW)

        lbl02 = Label(self, text='Range')
        lbl02.grid(row=0, column=2, padx=5, pady=5, sticky=EW)

        lbl2 = Label(self, text='Vbus')
        lbl2.grid(row=1, column=0, padx=5, pady=5, sticky=E)

        self.sh_conv_time_cb = ttk.Combobox(
            self, width=8, values=adc_conv_time)
        self.sh_conv_time_cb.grid(row=1, column=1, padx=20, sticky="E")
        self.sh_conv_time_cb.set(adc_conv_time[2])

        self.bus_vrange_cb = ttk.Combobox(
            self, width=8, values=bus_vrange)
        self.bus_vrange_cb.grid(row=1, column=2, padx=20, sticky="E")
        self.bus_vrange_cb.set(bus_vrange[1])

        lbl3 = Label(self, text='Vshunt')
        lbl3.grid(row=2, column=0, padx=5, pady=5, sticky=E)

        self.bus_conv_time_cb = ttk.Combobox(
            self, width=8, values=adc_conv_time)
        self.bus_conv_time_cb.grid(row=2, column=1, padx=20, sticky="E")
        self.bus_conv_time_cb.set(adc_conv_time[3])

        self.sh_vrange_cb = ttk.Combobox(
            self, width=8, values=sh_vrange)
        self.sh_vrange_cb.grid(row=2, column=2, padx=20, sticky="E")
        self.sh_vrange_cb.set(sh_vrange[0])

        lbl4 = Label(self, text='Mode')
        lbl4.grid(row=3, column=0, padx=5, pady=5, sticky=E)

        self.sh_conv_mode_cb = ttk.Combobox(
            self, width=8, values=adc_conv_mode)
        self.sh_conv_mode_cb.grid(
            row=3, column=1, padx=20, pady=10, sticky="EW")
        self.sh_conv_mode_cb.set(adc_conv_mode[1])

        chk0 = Checkbutton(self, text='Vbus', variable=self.chk_var)
        chk0.grid(row=4, column=0)

        self.btn_apply = Button(
            self, text='Apply', width=10, command=self.testReadDevice)
        self.btn_apply.grid(
            row=5, column=1, padx=10, pady=10, sticky=EW)

        if self.DEBUG:
            self.test_btn = Button(self, text='Read test',
                                   width=10, command=self.testReadDevice)
            self.test_btn.grid(row=6, column=1, padx=5, pady=20, columnspan=1)
            self.test_lbl = Label(
                self, text="Debug message:", anchor=W, justify='left')
            self.test_lbl.grid(row=6, column=2, padx=5,
                               pady=20, sticky=EW, columnspan=3)

    def testReadDevice(self):
        print('Read Test')
        self.comm.send('rr 0')
        resp = self.comm.response()
        testParams = self.get_states()
        testParams.append(resp)
        self.test_lbl.config(text=testParams)


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
                '''
        showinfo('About', aboutMsg)

    root = Tk()
    root.title('Digital Power Monitoring (DPM) Dashboard App')

    comm = boardcom.BoardComm()   # create an instance of class Comm
    du = dubrovnik.Dubrovnik()

    portList = comm.findPorts()
    comport = portList[0]

    # TODO Eventually migrate to a format where MainWindow is in itw own class
    # window = MainWindow(root)

# ******************************************
# ******             TABS           ********
# ******************************************
    tabControl = ttk.Notebook(root)

    tab1 = ttk.Frame(tabControl)
    tab2 = ttk.Frame(tabControl)
    tab3 = ttk.Frame(tabControl)

    tabControl.add(tab1, text='Measurements')
    tabControl.add(tab2, text='DPM Configuration')
    tabControl.add(tab3, text='Connection')
    tabControl.grid(row=0, column=0, columnspan=3, padx=10, pady=5, sticky=EW)

# *******************************************
# ****** Serial Communications Tab ********
# *******************************************
    serCom = SerComFrame(tab3, DEBUG=SERCOM_DBG)  # invoking the class
    # serCom.pack(side=TOP, fill=BOTH)
    serCom.grid_propagate(0)
    serComFrm_height = 60
    if SERCOM_DBG:
        serCom.config(width=350, height=serComFrm_height +
                      40, bd=4, relief=RIDGE)
    else:
        serCom.config(width=350, height=serComFrm_height, bd=2, relief=GROOVE)
    serCom.grid(row=1, column=0, padx=10, pady=4, sticky=NW)
    serCom.combo.set(portList[0])
    serCom.comm = comm

# *******************************
# ****** Measurement Tab ********
# *******************************
    measTab = MeasurementFrame(tab1, DEBUG=MEAS_TAB_DBG)  # invoking the class
    # program.pack(side=LEFT, fill=BOTH)
    measTab.grid_propagate(0)
    dpmFrm_height = 280
    if MEAS_TAB_DBG:
        measTab.config(width=580, height=dpmFrm_height+40, bd=4, relief=RIDGE)
    else:
        measTab.config(width=580, height=dpmFrm_height, bd=2, relief=FLAT)
    measTab.grid(row=2, column=0, padx=10, pady=4, sticky=NW)
    measTab.comm = comm   # initializeing self.com in DpmMain class

# ******************************
# ****** DPM Config Tab ********
# ******************************
    measTab = ConfigFrame(tab2, DEBUG=CFG_TAB_DBG)  # invoking the class
    # program.pack(side=LEFT, fill=BOTH)
    measTab.grid_propagate(0)
    dpmFrm_height = 300
    if CFG_TAB_DBG:
        measTab.config(width=580, height=dpmFrm_height+40, bd=4, relief=RIDGE)
    else:
        measTab.config(width=580, height=dpmFrm_height, bd=2, relief=FLAT)
    measTab.grid(row=2, column=0, padx=10, pady=4, sticky=NW)
    measTab.comm = comm   # initializeing self.com in DpmMain class

# ***************************
# ****** Status Bar *********
# ***************************
    stsBarComm = Label(root, text='Not connected', font=(
        "Helvetica", 9), anchor=W, justify=LEFT, pady=2)
    stsBarComm.config(bd=1, relief=SUNKEN)
    # stsBarComm.pack(side=BOTTOM, fill=X, anchor=W, padx=10, pady=10)
    stsBarComm.grid_propagate(0)
    stsBarComm.grid(row=4, column=0, padx=10, pady=5,
                    columnspan=3, sticky=EW)

    # ********** MENU ***********
    my_menu = Menu(root)
    root.config(menu=my_menu)

    # file_menu = Menu(my_menu, tearoff=False)
    # my_menu.add_cascade(label="File", menu=file_menu)
    # file_menu.add_command(label="New")
    # file_menu.add_command(label="Open")
    # file_menu.add_command(label="Save")
    # file_menu.add_command(label="Save As")
    # file_menu.add_separator()
    # file_menu.add_command(label="Exit")

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

    # ********** Load Configuration ***********
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

        if comm.isFlashPresent() == 0:
            showwarning(
                'Warning', 'No flash device detected\nInstall a device and RESET the board')

    stsBarComm.config(text=serCom.serParams)

    mainloop()

import os
import json
from tkinter.messagebox import showerror, showinfo
from tkinter import *
from tkinter import ttk
from dubLibs import boardcom
from dubLibs import dpm

SERCOM_DBG = False
MEAS_TAB_DBG = False
CFG_TAB_DBG = False


class SerComFrame(Frame):
    def __init__(self, parent=None, DEBUG=False):
        LabelFrame.__init__(self, parent, text='Serial Connection',
                            padx=10, pady=10)
        self.DEBUG = DEBUG
        self.STANDALONE = False
        self.comm = None   # object created by boardcom
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
        # create foldername string
        self.dpmConfigPath = f'{appData}\\DPM'
        if not os.path.isdir(self.dpmConfigPath):  # if folder doesn't exist
            # print(self.dpmConfigPath)
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

    def connectPort(self, defaultPort=None, checkIsDpmPresent=True):
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
            stsBarFrm.config(text=self.serParams)

        elif self.portStatus == 'connected':
            # if connected, disconnect from the current port
            self.disconnectPort(self.selPort)
            self.btn2['text'] = 'Connect'  # update button label
            self.portStatus = 'disconnected'  # update connection status
            stsBarFrm.config(text='Disconnected')
        else:
            print('No such port. Try again!!!')
        self.saveConfig()

    def disconnectPort(self, selPort):
        self.comm.disconnect(selPort)
        # print(f"Port: {selPort} disconnected")
        stsBarFrm.config(text='No COM port found!')

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
        dpm.brng = 2
        dpm.pg = 3
        dpm.badc = 3
        dpm.sadc = 3
        dpm.mode = 7
        dpm.rshunt = 0.1
        # update the GUI to reflect the values loaded from the file
        self.set_gui_config_params()

    def saveConfig(self):
        cfg = {'autoConnect': serCom.chk_var.get(),
               'lastUsedPort': serCom.selPort,
               'vbus_range': dpm.brng,
               'vshunt_range': dpm.pg,
               'bus_conv_time': dpm.badc,
               'sht_conv_time': dpm.sadc,
               'mode': dpm.mode,
               #    'rshunt_ohm': float(dpm.rshunt)
               'rshunt_ohm': dpm.rshunt
               }
        with open(f'{self.dpmConfigPath}\dpm.cfg', 'w') as fh:
            json.dump(cfg, fh, indent=3)

    def loadConfig(self):
        fname = f'{self.dpmConfigPath}\dpm.cfg'
        try:
            fname = open(fname, 'r')
            cfg = json.load(fname)  # get configuration from .cfg file
            serCom.autoConnect = cfg['autoConnect']  # get autoConnect config
            serCom.chk_var.set(serCom.autoConnect)   # ...set checkbox
            serCom.selPort = cfg['lastUsedPort']     # get last used port
            serCom.lastUsedPort = serCom.selPort     # ...set it
            # read saved config values and update dmp attributes
            dpm.brng = cfg['vbus_range']
            dpm.pg = cfg['vshunt_range']
            dpm.badc = cfg['bus_conv_time']
            dpm.sadc = cfg['sht_conv_time']
            dpm.mode = cfg['mode']
            dpm.rshunt = float(cfg['rshunt_ohm'])
            # update the GUI to reflect the values loaded from the file
            self.set_gui_config_params()
            fname.close()
        except FileNotFoundError:
            self.loadDefaultSettings()
            self.saveConfig()

    def set_gui_config_params(self):
        configFrm.bus_vrange_cb.set(configFrm.bus_vrange[dpm.brng])
        configFrm.sh_vrange_cb.set(configFrm.sh_vrange[dpm.pg])
        configFrm.bus_conv_time_cb.set(configFrm.adc_conv_time[dpm.badc])
        configFrm.sh_conv_time_cb.set(configFrm.adc_conv_time[dpm.sadc])
        configFrm.conv_mode_cb.set(configFrm.adc_conv_mode[dpm.mode])
        configFrm.rshunt_var.set(dpm.rshunt)

    def testSerComm(self):
        serParams = '%s, baud=%d, bytes=%1d,\nparity=%s, stop=%1d, protocol=%s' \
            % (self.comPort, self.comBaudrate, self.comBytesize, self.comParity, self.comStopbits, self.comXonXoff)
        self.test_lbl.config(text=serParams)


class MeasurementFrame(Frame):

    def __init__(self, parent=None, DEBUG=False):
        # LabelFrame.__init__(self, parent, text='Measurements', padx=5, pady=5)
        LabelFrame.__init__(self, parent, padx=5, pady=5)
        self.DEBUG = DEBUG
        self.comm = None
        self.meas_in_progress = False

        self.buildFrame()

    def buildFrame(self):
        # ROW 1. Labels for: shunt voltage, measurement value and unit
        Label(self, text='Vshunt').grid(
            row=0, column=0, padx=5, pady=5, sticky=E)
        self.vshunt_lbl = Label(self, text="0", relief='sunken', width=20,
                                anchor=E, fg='black', bg='#f8f8f8', font=('Calibri', 12))
        self.vshunt_lbl.grid(row=0, column=1, padx=5, pady=10, sticky=EW)
        Label(self, text='mV').grid(row=0, column=2, padx=10, pady=5, sticky=W)

        # ROW 2. Labels for: bus voltage, measurement value  and unit
        Label(self, text='Vbus').grid(
            row=1, column=0, padx=5, pady=5, sticky=E)

        self.vbus_lbl = Label(self, text="0", relief='sunken', width=20,
                              anchor=E, fg='black', bg='#f8f8f8', font=('Calibri', 12))
        self.vbus_lbl.grid(row=1, column=1, padx=5,
                           pady=10, sticky=EW)
        Label(self, text='V').grid(row=1, column=2, padx=10, pady=5, sticky=W)

        # ROW 3. Labels for: current, value and unit
        Label(self, text='Current').grid(
            row=2, column=0, padx=5, pady=5, sticky=E)
        self.i_lbl = Label(self, text="0", relief='sunken', width=20,
                           anchor=E, fg='black', bg='#f8f8f8', font=('Calibri', 12))
        self.i_lbl.grid(row=2, column=1, padx=5, pady=10, sticky=EW)
        Label(self, text='A').grid(row=2, column=2, padx=10, pady=5, sticky=W)

        # ROW 4. Labels for: power, value and unit
        Label(self, text='Power').grid(
            row=3, column=0, padx=5, pady=5, sticky=E)
        self.p_lbl = Label(self, text="0", relief='sunken', width=20,
                           anchor=E, fg='black', bg='#f8f8f8', font=('Calibri', 12))
        self.p_lbl.grid(row=3, column=1, padx=5, pady=10, sticky=EW)
        Label(self, text='mW').grid(row=3, column=2, padx=10, pady=5, sticky=W)

        self.btn_start_meas = Button(
            self, text='START', width=10, font=('Calibri bold', 18), command=self.start_stop)
        self.btn_start_meas.grid(
            row=4, column=1, padx=10, pady=10, sticky=EW)

        if self.DEBUG:
            self.test_btn = Button(self, text='Reg Values',
                                   width=10, command=self.test_func)
            self.test_btn.grid(row=6, column=0, padx=5, pady=10, columnspan=1)
            self.test_lbl = Label(
                self, text="debug message", anchor=W, justify='center')
            self.test_lbl.grid(row=6, column=1, padx=5,
                               pady=10, sticky=EW, columnspan=3)
            # Print parameters available for a Tkinter Label
            print(self.test_lbl.configure().keys())
            # self.test_lbl['relief'] = 'sunken'
            # self.test_lbl['bg'] = '#fff'
            self.test_lbl.config(relief='sunken', bg='#fff',
                                 width=40, font=('Calibri', 11))

    def start_stop(self):

        if dpm.mode == 0 or dpm.mode == 4:
            # Power Down, ADC Off
            self.get_a_measurement(0, 0, 0, 0)
            self.meas_in_progress = False
            self.btn_start_meas.config(text='START', fg='black')

        elif dpm.mode == 1:
            # Vshunt Triggered
            self.get_a_measurement(1, 0, 1, 0)
            self.meas_in_progress = False
            self.btn_start_meas.config(text='START', fg='black')

        elif dpm.mode == 2:
            # Vbus Triggered
            self.get_a_measurement(0, 1, 0, 0)
            self.meas_in_progress = False
            self.btn_start_meas.config(text='START', fg='black')

        elif dpm.mode == 3:
            # Vshunt+Vbus Triggered
            self.get_a_measurement(1, 1, 1, 1)
            self.meas_in_progress = False
            self.btn_start_meas.config(text='START', fg='black')

        else:
            if not self.meas_in_progress:
                self.meas_in_progress = True
                self.btn_start_meas.config(
                    text='STOP', fg='red')
                self.get_a_measurement(1, 1, 1, 1)
                self.update_measurement()
            else:
                self.meas_in_progress = False
                self.btn_start_meas.config(text='START', fg='black')

    # Interrupt at periodic intervals
    def update_measurement(self):
        if self.meas_in_progress:
            self.get_a_measurement(1, 1, 1, 1)
            root.after(500, self.update_measurement)

    # TODO may add parameters which measurements to take
    def get_a_measurement(self, get_vs, get_vb, get_i, get_p):

        # TODO To clear the conversion ready bit must write to config reg or read power
        # This can be done multiple places, for now I put it here
        # May be put into the start_stop function
        dpm.set_config()  # Clear CNVR Conversion Ready (Bit 1)
        # dpm.set_calibration()  # this is probably not needed. Only when updating config regs

        if get_vs:
            v_sh = dpm.read_shunt_voltage()
            if v_sh > dpm.vshunt_range_tbl[dpm.pg]:
                self.vshunt_lbl.config(fg='red')
            else:
                self.vshunt_lbl.config(fg='black')
            self.vshunt_lbl['text'] = f'{1e3*v_sh:0.3f}'

        if get_vb:
            v_b = dpm.read_bus_voltage()
            if v_b > dpm.vbus_range_tbl[dpm.brng]:
                self.vbus_lbl.config(fg='red')
            else:
                self.vbus_lbl.config(fg='black')
            self.vbus_lbl['text'] = f'{v_b:0.3f}'

        if get_i:
            cur = dpm.read_current()
            self.i_lbl.config(text=f'{cur:0.3f}')

        if get_p:
            pwr = dpm.read_power()
            self.p_lbl.config(text=f'{pwr:0.3f}')

    def test_func(self):
        vals = dpm.readRegisters()
        self.test_lbl.config(text=vals)
        # print(f'vbus = {dpm.read_bus_voltage():.3f}V ', end='')
        # print(f'vshunt = {dpm.read_shunt_voltage():.3f}V ', end='')
        # print(f'current = {dpm.read_current():.3f}A ', end='')
        # print(f'power = {dpm.read_power():.2f}mW ')
        # print(dpm.brng, dpm.pg, dpm.badc, dpm.sadc, dpm.mode, dpm.rshunt)


class ConfigFrame(Frame):

    def __init__(self, parent=None, DEBUG=False):
        LabelFrame.__init__(self, parent, text='Configuration', padx=5, pady=5)
        # self.pack(side=TOP, anchor=NW, padx=10, pady=10)
        self.DEBUG = DEBUG
        self.comm = None
        self.rshunt_var = IntVar()
        self.chk_var = IntVar()
        self.adc_conv_time = ['72us', '132us', '258us', '508us', '1.01ms',
                              '2.01ms', '4.01ms', '8.01ms', '16.01ms', '32.01ms', '64.01ms']
        self.bus_vrange = ['16V', '32V', '60V']
        self.sh_vrange = ['40mV', '80mV', '160mV', '320mV']
        self.adc_conv_mode = ['Power-down', 'Shunt voltage (trig)',
                              'Bus voltge (trig)', 'Shunt and Bus (trig)',
                              'ADC off (disabled)', 'Shunt voltage (cont)',
                              'Bus voltge (cont)', 'Shunt and Bus (cont)']

        # *** THIS MUST BE THE VERY LAST COMMAND ***
        self.buildFrame()

    def buildFrame(self):
        # create widgets
        Label(self, text='Conv. Time').grid(
            row=0, column=1, padx=5, pady=5, sticky=EW)

        Label(self, text='Range').grid(
            row=0, column=2, padx=5, pady=5, sticky=EW)

        Label(self, text='Vbus').grid(
            row=1, column=0, padx=5, pady=5, sticky=E)

        Label(self, text='Vshunt').grid(
            row=2, column=0, padx=5, pady=5, sticky=E)

        Label(self, text='Mode').grid(
            row=3, column=0, padx=5, pady=5, sticky=E)

        self.bus_conv_time_cb = ttk.Combobox(
            self, width=8, values=self.adc_conv_time)
        self.bus_conv_time_cb.grid(row=1, column=1, padx=20, sticky="E")
        self.bus_conv_time_cb.set(self.adc_conv_time[3])

        self.bus_vrange_cb = ttk.Combobox(
            self, width=8, values=self.bus_vrange, postcommand=self.updtRegs)
        self.bus_vrange_cb.grid(row=1, column=2, padx=20, sticky="E")
        self.bus_vrange_cb.set(self.bus_vrange[1])

        self.sh_conv_time_cb = ttk.Combobox(
            self, width=8, values=self.adc_conv_time)
        self.sh_conv_time_cb.grid(row=2, column=1, padx=20, sticky="E")
        self.sh_conv_time_cb.set(self.adc_conv_time[2])

        self.sh_vrange_cb = ttk.Combobox(
            self, width=8, values=self.sh_vrange)
        self.sh_vrange_cb.grid(row=2, column=2, padx=20, sticky="E")
        self.sh_vrange_cb.set(self.sh_vrange[0])

        self.conv_mode_cb = ttk.Combobox(
            self, width=8, values=self.adc_conv_mode, justify='center')
        self.conv_mode_cb.grid(
            row=3, column=1, columnspan=2, padx=20, pady=10, sticky="EW")
        self.conv_mode_cb.set(self.adc_conv_mode[7])

        Label(self, text='Rshunt Value').grid(
            row=4, column=0, padx=5, pady=5, sticky=E)
        self.ent_rshunt = Entry(self, justify=RIGHT,
                                textvariable=self.rshunt_var)
        self.ent_rshunt.grid(row=4, column=1, columnspan=2,
                             padx=20, pady=10, sticky='WE')
        Label(self, text='Ohm', justify=LEFT).grid(
            row=4, column=3, pady=5, sticky=W)
        self.rshunt_var.set('1.0')

        # chk0 = Checkbutton(self, text='Vbus', variable=self.chk_var)
        # chk0.grid(row=5, column=0)

        Label(self, text='Config Reg').grid(
            row=5, column=0, padx=5, pady=5, sticky=E)
        self.cfg_reg_lbl = Label(
            self, text='', anchor=W)
        # self.cfg_reg_lbl = Label(
        #     self, text="R BR PG ADC1 ADC2 MOD [FFFFh]", anchor=W, justify='center')
        self.cfg_reg_lbl.grid(row=5, column=1, padx=20,
                              pady=5, sticky=EW, columnspan=2)
        self.cfg_reg_lbl.config(relief=GROOVE, width=24, font=('Calibri', 11))

        self.btn_apply = Button(
            self, text='Apply', width=10, command=self.apply_dpm_config)
        self.btn_apply.grid(
            row=6, column=1, padx=10, pady=2, sticky=EW)

        if self.DEBUG:
            self.test_btn = Button(self, text='Read test',
                                   width=10, command=self.testRead)
            self.test_btn.grid(row=7, column=0, padx=5, pady=20, columnspan=1)
            self.test_lbl = Label(
                self, text="debug message", anchor=W)
            self.test_lbl.grid(row=7, column=1, padx=5,
                               pady=30, sticky=EW, columnspan=3)
            self.test_lbl.config(relief='sunken', bg='#fff',
                                 width=40, font=('Calibri', 11))

    def apply_dpm_config(self):
        # get config parameters from GUI and update dpm attributes
        dpm.brng = self.bus_vrange_cb.current()
        dpm.pg = self.sh_vrange_cb.current()
        dpm.badc = self.bus_conv_time_cb.current()
        dpm.sadc = self.sh_conv_time_cb.current()
        dpm.mode = self.conv_mode_cb.current()
        dpm.rshunt = float(self.ent_rshunt.get())
        print(f'rshunt type: {type(dpm.rshunt)}, value:{dpm.rshunt}')

        # TODO check this. Should it be here or in 'start_stop'?

        measFrm.meas_in_progress = False
        measFrm.btn_start_meas.config(text='START', fg='black')
        # Actions to do depending on the value of the MODE BITS
        if dpm.mode == 0 or dpm.mode == 4:
            # Power Down, ADC OFF
            measFrm.vshunt_lbl.config(text='---', state=DISABLED, bg='#e0e0e0')
            measFrm.vbus_lbl.config(text='---', state=DISABLED, bg='#e0e0e0')
            measFrm.i_lbl.config(text='---', state=DISABLED, bg='#e0e0e0')
            measFrm.p_lbl.config(text='---', state=DISABLED, bg='#e0e0e0')

        elif dpm.mode == 1 or dpm.mode == 5:
            measFrm.vshunt_lbl.config(text='---', state=NORMAL, bg='#f8f8f8')
            measFrm.vbus_lbl.config(text='---', state=DISABLED, bg='#e0e0e0')
            measFrm.i_lbl.config(text='---', state=NORMAL, bg='#f8f8f8')
            measFrm.p_lbl.config(text='---', state=DISABLED, bg='#e0e0e0')

        elif dpm.mode == 2 or dpm.mode == 6:
            measFrm.vshunt_lbl.config(text='---', state=DISABLED, bg='#e0e0e0')
            measFrm.vbus_lbl.config(text='---', state=NORMAL, bg='#f8f8f8')
            measFrm.i_lbl.config(text='---', state=DISABLED, bg='#e0e0e0')
            measFrm.p_lbl.config(text='---', state=DISABLED, bg='#e0e0e0')

        else:
            measFrm.vshunt_lbl.config(text='---', state=NORMAL, bg='#f8f8f8')
            measFrm.vbus_lbl.config(text='---', state=NORMAL, bg='#f8f8f8')
            measFrm.i_lbl.config(text='---', state=NORMAL, bg='#f8f8f8')
            measFrm.p_lbl.config(text='---', state=NORMAL, bg='#f8f8f8')

        # save values into file
        serCom.saveConfig()
        # b = f'0|{dpm.brng:02b}|{dpm.pg:02b}|{dpm.badc:04b}|{dpm.sadc:04b}|{dpm.mode:03b}'
        b = f'0 {dpm.brng:02b} {dpm.pg:02b} {dpm.badc:04b} {dpm.sadc:04b} {dpm.mode:03b}'
        w = (dpm.brng << 13) | (dpm.pg << 11) | (
            dpm.badc << 7) | (dpm.sadc << 3) | dpm.mode
        msg = b + f' = {w:04X}h'
        self.cfg_reg_lbl.config(text=msg)
        # program DPM registers with values set in GUI
        print(
            f'brng={dpm.brng}, pg={dpm.pg}, badc={dpm.badc}, sadc={dpm.sadc}, mode={dpm.mode},rval={dpm.rshunt}')
        dpm.set_config()
        dpm.set_calibration()

    def updtRegs(self):
        print('selection made')

    def testRead(self):
        # print(dpm.readRegisters())  # prints the values of 10 registers
        # displays the values of configuration Tab in this label
        vals = f'brng={dpm.brng}, pg={dpm.pg}, badc={dpm.badc}, sadc={dpm.sadc}, mode={dpm.mode},rval={dpm.rshunt}'
        self.test_lbl.config(text=vals)


if __name__ == "__main__":

    # def updtStsBar(statusMsg):
    #     print(statusMsg)
    #     stsBarComm.config(text=statusMsg)

    def showAbout():
        aboutMsg = '''
                   *************************
                   *** DPM EVK Dashboard ***
                   *************************

                   Ver 0.8
                   Authors: 
                   Csaba Moldvai, Eyal Barzilay
                '''
        showinfo('About', aboutMsg)

    root = Tk()
    root.title('Digital Power Monitoring (DPM) Dashboard App')

    cm = boardcom.BoardComm()   # create an instance of class Comm
    dpm = dpm.DpmEK(cm)         # create an instance of class DpmEK

    portList = cm.findPorts()
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
    serCom.comm = cm

# *******************************
# ****** Measurement Tab ********
# *******************************
    measFrm = MeasurementFrame(tab1, DEBUG=MEAS_TAB_DBG)  # invoking the class
    # program.pack(side=LEFT, fill=BOTH)
    measFrm.grid_propagate(0)
    y_mF = 280
    if MEAS_TAB_DBG:
        measFrm.config(width=580, height=y_mF+40, bd=4, relief=RIDGE)
    else:
        measFrm.config(width=580, height=y_mF, bd=2, relief=FLAT)
    measFrm.grid(row=2, column=0, padx=10, pady=4, sticky=NW)
    measFrm.comm = cm   # initializeing self.com in DpmMain class

# ******************************
# ****** DPM Config Tab ********
# ******************************
    configFrm = ConfigFrame(tab2, DEBUG=CFG_TAB_DBG)  # invoking the class
    # program.pack(side=LEFT, fill=BOTH)
    configFrm.grid_propagate(0)
    y_cF = 300
    if CFG_TAB_DBG:
        configFrm.config(width=580, height=y_cF +
                         40, bd=4, relief=RIDGE)
    else:
        configFrm.config(width=580, height=y_cF, bd=2, relief=FLAT)
    configFrm.grid(row=2, column=0, padx=10, pady=4, sticky=NW)
    configFrm.comm = cm   # initializeing self.com in DpmMain class

# ***************************
# ****** Status Bar *********
# ***************************
    stsBarFrm = Label(root, text='Not connected', font=(
        "Helvetica", 9), anchor=W, justify=LEFT, pady=2)
    stsBarFrm.config(bd=1, relief=SUNKEN)
    # stsBarComm.pack(side=BOTTOM, fill=X, anchor=W, padx=10, pady=10)
    stsBarFrm.grid_propagate(0)
    stsBarFrm.grid(row=4, column=0, padx=10, pady=5,
                   columnspan=3, sticky=EW)

    # ********** MENU ***********
    my_menu = Menu(root)
    root.config(menu=my_menu)

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
                                   checkIsDpmPresent=False)
        else:
            # otherwise connect to the first in the list
            serCom.connectPort(portList[0], checkIsDpmPresent=False)
    # If not autoconnect then do not connect to anything

    stsBarFrm.config(text=serCom.serParams)

    root.mainloop()

import os
import json
import tkinter as tk
from tkinter import ttk
from tkinter import simpledialog
from tkinter.messagebox import showerror, showinfo
from dubLibs import boardcom
from dubLibs import dpm

MEAS_TAB_DBG = False
CFG_TAB_DBG = False
SERCOM_DBG = False

comFrm = None
measFrm = None
configFrm = None
stsBar = None
dp = None


class App(tk.Tk):
    def __init__(self, title, size):
        super().__init__()

        global dp
        self.title(title)
        if MEAS_TAB_DBG:
            self.geometry(f'{size[0]}x{size[1]+30}')
        else:
            self.geometry(f'{size[0]}x{size[1]}')

        self.minsize(size[0], size[1])
        self.resizable(False,False)

        cm = boardcom.BoardComm()   # create an instance of class Comm
        dp = dpm.DpmEK(cm)         # create an instance of class DpmEK

        portList = cm.findPorts()

    # ******************************************
    # ******             TABS           ********
    # ******************************************
        tabs = ttk.Notebook(self)

        tab1 = ttk.Frame(tabs)
        tab2 = ttk.Frame(tabs)
        tab3 = ttk.Frame(tabs)

        tabs.add(tab1, text='Measurements')
        tabs.add(tab2, text='DPM Configuration')
        tabs.add(tab3, text='Connection')
        # tabs.grid(row=0, column=0, columnspan=3, padx=10, pady=5, sticky='')
        tabs.place(x=0,y=0,relheight=.92,relwidth=1)

    # *******************************
    # ****** Measurement Tab ********
    # *******************************
        global measFrm

        measFrm = MeasurementFrame(tab1, DEBUG=MEAS_TAB_DBG)  # invoking the class
        measFrm.comm = cm   # initializeing self.com in DpmMain class

    # ******************************
    # ****** DPM Config Tab ********
    # ******************************
        global configFrm

        configFrm = ConfigFrame(tab2, DEBUG=CFG_TAB_DBG)  # invoking the class
        configFrm.comm = cm   # initializeing self.com in DpmMain class

    # *******************************************
    # ****** Serial Communications Tab ********
    # *******************************************
        global comFrm

        comFrm = SerComFrame(tab3, DEBUG=SERCOM_DBG)  # invoking the class
        comFrm.combo.set(portList[0])
        comFrm.comm = cm

    # ***************************
    # ****** Status Bar *********
    # ***************************
        global stsBar

        stsFrm = ttk.Frame(self)
        stsFrm.place(relx=0,rely=0.92,relheight=.08,relwidth=1)

        stsBar = ttk.Label(stsFrm, text='Not connected', anchor='w', font=('Helvetica', 10))
        stsBar.pack(side='bottom', expand=True, fill='both', ipadx=5, ipady=2, padx=10)

        # ********** MENU ***********
        my_menu = tk.Menu(self)
        self.configure(menu=my_menu)

        config_menu = tk.Menu(my_menu, tearoff=False)
        my_menu.add_cascade(label="Config", menu=config_menu)
        config_menu.add_command(label="Load config", command=comFrm.loadConfig)
        config_menu.add_command(label="Store config",
                                command=comFrm.saveConfig)
        config_menu.add_command(label="Restore defaults",
                                command=comFrm.loadDefaultSettings)

        help_menu = tk.Menu(my_menu, tearoff=False)
        my_menu.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="Help")
        help_menu.add_separator()
        help_menu.add_command(label="About", command=self.show_about)

        # ********** Load Configuration ***********
        comFrm.loadConfig()  # includes autoConnect and lastUsedPort

        # * At this point we have a list of valid COM ports.
        # * Next step is to connect to one of them.
        if comFrm.autoConnect:  # if autoConnect set
            if len(portList) > 1:  # no need to check if ==0. boardcom.py already does
                if comFrm.lastUsedPort in portList:  # if last used port is in the portList
                    # connect to that port
                    comFrm.connectPort(comFrm.lastUsedPort)
            else:
                # otherwise connect to the first in the list
                comFrm.connectPort(portList[0])
        # If not autoconnect then do not connect to anything
        stsBar.configure(text=comFrm.serParams)

        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.mainloop()

    def on_closing(self):
        # comFrm.saveConfig()
        self.destroy()

    def show_about(self):
        about_msg = '''
        *************************
        *** DPM EVK Dashboard ***
        *************************

        Ver 0.72 (Classic)
        Requires updated dpm.py with changed function names (prog_ instead of set_)
        Added Calibration Reg label

        Authors:
        Csaba Moldvai, Eyal Barzilay
        '''
        showinfo('About', about_msg)


class SerComFrame(ttk.Frame):

    global comFrm  # ! Check global
    # global dp

    def __init__(self, parent=None, DEBUG=False):
        super().__init__(parent)

        # 'self' in this context is CTkFrame, so we can configure it
        # ! self.configure(bg='transparent')
        self.place(x=0,y=0,relwidth=1,relheight=.8)

        self.DEBUG = DEBUG
        self.STANDALONE = False
        self.comm = None   # object created by boardcom
        self.portStatus = 'disconnected'
        self.selPort = ''  # keeps track of the selected port, between calls
        self.lastUsedPort = None
        self.portList = []
        self.portHandle = None
        self.chk_var = tk.IntVar()
        self.autoConnect = 0
        self.serParams = ''

        # serial port parameter definitions
        self.comPort = None
        self.comBaudrate = None
        self.comBytesize = None
        self.comParity = None
        self.comStopbits = None
        self.comXonXoff = None

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
        comFrm = ttk.Frame(self)
        comFrm.place(relx=0.05, rely=0.1, relwidth=.6, relheight=.8)
        # comFrm.pack(expand=True, fill='both')
        comFrm.columnconfigure((0, 1, 2), weight=1)

        chk = tk.Checkbutton(comFrm, text='Auto connect', variable=self.chk_var, font=('Helvetica', 10))
        self.combo = ttk.Combobox(comFrm, values=self.portList, postcommand=self.updtPortList, font=('Helvetica', 10))
        self.btn2 = tk.Button(comFrm, text='Connect', width=10, command=self.connectPort, font=('Helvetica', 10))

        chk.grid(row=0, column=0, pady=20)
        self.combo.grid(row=0, column=1, padx=10, pady=20)
        self.btn2.grid(row=0, column=2, padx=10, pady=20)

        if self.STANDALONE:
            self.btn3 = ttk.Button(comFrm, text='Save Config',command=self.saveConfig)
            self.btn3.grid(row=0, column=3, padx=10, sticky='e')

        if self.DEBUG:
            self.test_btn = ttk.Button(comFrm, text='Testing', command=self.testSerComm)
            self.test_lbl = ttk.Label(comFrm, text="Debug message:", anchor='w', justify='left')

            self.test_btn.grid(row=1, column=0, padx=5, pady=10, columnspan=1)
            self.test_lbl.grid(row=1, column=1, padx=5, pady=10, sticky='we', columnspan=3)

    def updtPortList(self):
        self.portList = self.comm.findPorts()
        self.combo['values'] = self.portList
        self.combo.set(self.portList[0])

    def connectPort(self, defaultPort=None):
        if self.portStatus == 'disconnected':
            if defaultPort:
                self.selPort = defaultPort  # updates class variable as well
                self.combo.set(self.selPort)
            else:
                self.selPort = self.combo.get()
            # only if disconnected, connect to selected port
            self.portHandle = self.comm.connect(self.selPort)
            self.setSerialParams()
            self.btn2.configure(text='Disconnect')  # change button label
            self.portStatus = 'connected'  # update connection status
            # self.serParams = f'Connected: {self.comPort} ({self.comBaudrate},{self.comBytesize},{self.comParity},{self.comStopbits},{self.comXonXoff})'
            self.serParams = f'Connected: {self.comPort}, {self.comBaudrate} bps'
            stsBar.configure(text=self.serParams)

        elif self.portStatus == 'connected':
            # if connected, disconnect from the current port
            self.disconnectPort(self.selPort)
            self.btn2.configure(text='Connect')  # update button label
            self.portStatus = 'disconnected'  # update connection status
            stsBar.configure(text='Disconnected')
        else:
            print('No such port. Try again!!!')
        self.saveConfig()

    def disconnectPort(self, selPort):
        self.comm.disconnect(selPort)
        # print(f"Port: {selPort} disconnected")
        stsBar.configure(text='No COM port found!')

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
        comFrm.chk_var.set(0)
        comFrm.selPort = ''
        dp.brng = 2
        dp.pg = 3
        dp.badc = 3
        dp.sadc = 3
        dp.mode = 7
        dp.rshunt = 0.1
        # update the GUI to reflect the values loaded from the file
        self.set_gui_config_params()

    def saveConfig(self):
        cfg = {'autoConnect': comFrm.chk_var.get(),
               'lastUsedPort': comFrm.selPort,
               'vbus_range': dp.brng,
               'vshunt_range': dp.pg,
               'bus_conv_time': dp.badc,
               'sht_conv_time': dp.sadc,
               'mode': dp.mode,
               #    'rshunt_ohm': float(dp.rshunt)
               'rshunt_ohm': dp.rshunt
               }
        with open(f'{self.dpmConfigPath}\dpm.cfg', 'w') as fh:
            json.dump(cfg, fh, indent=3)

    def loadConfig(self):
        fname = f'{self.dpmConfigPath}\dpm.cfg'
        try:
            fname = open(fname, 'r')
            cfg = json.load(fname)  # get configuration from .cfg file
            self.autoConnect = cfg['autoConnect']  # get autoConnect config
            self.chk_var.set(self.autoConnect)   # ...set checkbox
            self.selPort = cfg['lastUsedPort']     # get last used port
            self.lastUsedPort = self.selPort     # ...set it

            # read saved config values and update dmp attributes
            dp.brng = cfg['vbus_range']
            dp.pg = cfg['vshunt_range']
            dp.badc = cfg['bus_conv_time']
            dp.sadc = cfg['sht_conv_time']
            dp.mode = cfg['mode']
            dp.rshunt = float(cfg['rshunt_ohm'])
            # update the GUI to reflect the values loaded from the file
            self.set_gui_config_params()
            fname.close()
        except FileNotFoundError:
            self.loadDefaultSettings()
            self.saveConfig()

    def set_gui_config_params(self):
        '''Gets the dp paramter values from dpm class and sets widget values to the current state'''
        configFrm.bus_vrange_cb.set(configFrm.bus_vrange[dp.brng])
        configFrm.sh_vrange_cb.set(configFrm.sh_vrange[dp.pg])
        configFrm.bus_conv_time_cb.set(configFrm.adc_conv_time[dp.badc])
        configFrm.sh_conv_time_cb.set(configFrm.adc_conv_time[dp.sadc])
        configFrm.conv_mode_cb.set(configFrm.adc_conv_mode[dp.mode])
        # configFrm.rshunt_var.set(dp.rshunt)
        configFrm.ent_rshunt.configure(text=dp.rshunt)
        # Aslo update the Config Register Label with fresh values
        configFrm.set_config_reg_label()

    def testSerComm(self):
        serParams = f'{self.comPort}, baud={self.comBaudrate}, bytes={self.comBytesize}, parity={self.comParity}, stop={self.comStopbits}, protocol={self.comXonXoff}'
        self.test_lbl.configure(text=serParams)


class MeasurementFrame(ttk.Frame):

    global dp

    def __init__(self, parent=None, DEBUG=False):
        super().__init__(parent)
        
        # 'self' in this context is CTkFrame, so we can configure it
        # ! self.configure(bg='transparent')
        self.pack(expand=True, fill='both')

        self.DEBUG = DEBUG
        self.comm = None
        self.meas_in_progress = False
        self.meas_rules = {
            # mode: [meas_vs, meas_vb, meas_i, meas_p, continue],
            0: [False, False, False, False, False],
            1: [True, False, True, False, False],
            2: [False, True, False, False, False],
            3: [True, True, True, True, False],
            4: [False, False, False, False, False],
            5: [True, False, True, False, True],
            6: [False, True, False, False, True],
            7: [True, True, True, True, True]}

        self.buildFrame()

    def buildFrame(self):
        measFrm = ttk.Frame(self)
        btnFrm = ttk.Frame(self)

        measFrm.place(relx=0, rely=0.1, relwidth=.6, relheight=.7)
        btnFrm.place(relx=0.6, rely=0.1, relwidth=.4, relheight=.7)

        # create the grid
        measFrm.rowconfigure((0, 1, 2, 3, 4), weight=1, uniform='a')
        measFrm.columnconfigure((0,2), weight=1)
        measFrm.columnconfigure(1, weight=2)

        # create and place column 0 labels: row titles
        ttk.Label(measFrm, text='Vshunt', font=('Helvetica', 10)).grid(row=0, column=0, padx=5, pady=5, sticky='e')
        ttk.Label(measFrm, text='Vbus', font=('Helvetica', 10)).grid(row=1, column=0, padx=5, pady=5, sticky='e')
        ttk.Label(measFrm, text='Current', font=('Helvetica', 10)).grid(row=2, column=0, padx=5, pady=5, sticky='e')
        ttk.Label(measFrm, text='Power', font=('Helvetica', 10)).grid(row=3, column=0, padx=5, pady=5, sticky='e')
        ttk.Label(measFrm, text='R load', font=('Helvetica', 10)).grid(row=4, column=0, padx=5, pady=5, sticky='e')

        # create column 1 labels: displays measurement values
        self.vshunt_lbl = ttk.Label(measFrm, text="---",anchor='e', width=20, relief='sunken', font=('Helvetica', 11))
        self.vbus_lbl = ttk.Label(measFrm, text="---", anchor='e', width=20, relief='sunken', font=('Helvetica',11))
        self.i_lbl = ttk.Label(measFrm, text="---", anchor='e', width=20, relief='sunken', font=('Helvetica',11))
        self.p_lbl = ttk.Label(measFrm, text="---", anchor='e', width=20, relief='sunken', font=('Helvetica',11))
        self.rload_lbl = ttk.Label(measFrm, text="---", anchor='e', width=20, relief='sunken', font=('Helvetica',11))
        
        # place column 1 labels
        self.vshunt_lbl.grid(row=0, column=1, padx=5, pady=10, sticky='we')
        self.vbus_lbl.grid(row=1, column=1, padx=5, pady=10, sticky='we')
        self.i_lbl.grid(row=2, column=1, padx=5, pady=10, sticky='we')
        self.p_lbl.grid(row=3, column=1, padx=5, pady=10, sticky='we')
        self.rload_lbl.grid(row=4, column=1, padx=5, pady=10, sticky='we')

        # create and place column 2 labels: units
        ttk.Label(measFrm, text='mV', font=('Helvetica', 10)).grid(row=0, column=2, padx=10, pady=5, sticky='w')
        ttk.Label(measFrm, text='V', font=('Helvetica', 10)).grid(row=1, column=2, padx=10, pady=5, sticky='w')
        self.i_mA_lbl = ttk.Label(measFrm, text='A', font=('Helvetica', 10))
        self.i_mA_lbl.grid(row=2, column=2, padx=10, pady=5, sticky='w')
        self.p_mW_lbl = ttk.Label(measFrm, text='mW', font=('Helvetica', 10))
        self.p_mW_lbl.grid(row=3, column=2, padx=10, pady=5, sticky='w')
        ttk.Label(measFrm, text='Ohm', font=('Helvetica', 10)).grid(row=4, column=2, padx=10, pady=5, sticky='w')

        # create and place the right side Frame for the START/STOP button
        self.btn_start_meas = tk.Button(btnFrm, text='START', width=10, font=('Helvetica bold', 16), command=self.start_stop)
        self.btn_start_meas.pack(expand=True, padx=10, pady=10, ipadx=10, ipady=20)

        if self.DEBUG:
            self.test_btn = ttk.Button(measFrm, text='Test Values', command=self.test_func)
            self.test_lbl = ttk.Label(measFrm, text="debug message", anchor='w')

            self.test_btn.grid(row=6, column=0, padx=5, pady=10, columnspan=1)
            self.test_lbl.grid(row=6, column=1, padx=5, pady=10, sticky='e', columnspan=3)
            # print parameters available for a tkinter Label
            # print(self.test_lbl.configure().keys())

    def start_stop(self):
        """When the START button was pressed start the measurement process. This function is rule driven \
            The rules are set in meas_rules dictionary"""

        if self.meas_in_progress:
            self.meas_in_progress = False
            self.btn_start_meas.configure(text='START')
            return

        rule_set = self.meas_rules[dp.mode]
        self.get_a_measurement(rule_set[0], rule_set[1], rule_set[2], rule_set[3])
        self.meas_in_progress = rule_set[4]
        if rule_set[4]:
            self.btn_start_meas.configure(text='STOP')
            self.after(500, self.update_measurement)
        else:
            self.btn_start_meas.configure(text='START')

    # Interrupt at periodic intervals
    def update_measurement(self):
        """At periodic intervals get a new measurement and display it on Measurement Tab"""
        if self.meas_in_progress:
            rule_set = self.meas_rules[dp.mode]
            self.get_a_measurement(rule_set[0], rule_set[1], rule_set[2], rule_set[3])
            self.after(500, self.update_measurement)

    def get_a_measurement(self, get_vs, get_vb, get_i, get_p):
        """Get a measurement for the items that are True in the argument list\
            For example, if get_vs=True, read the shunt voltage register and display it in the label\
            Before each measurement the CNVR (Conversion Ready) bit must be cleared."""
        dp.prog_config_reg()  # Clear CNVR Conversion Ready (Bit 1)

        # ! Not sure if this belongs here, but we need to initialize the chip after connecting (I guess)        
        dp.prog_calib_reg()   # Sometimes when starting the program we mesaure 0mA, 0mW, calib reg = 0x0

        if get_vs:
            v_sh = dp.read_shunt_voltage()
            if v_sh > dp.vshunt_range_tbl[dp.pg]:
                self.vshunt_lbl.configure(foreground='red', width=20)
            else:
                self.vshunt_lbl.configure(foreground='black', width=20)
            self.vshunt_lbl.configure(text=f'{1e3*v_sh:0.3f}')

        if get_vb:
            v_b = dp.read_bus_voltage()
            if v_b > dp.vbus_range_tbl[dp.brng]:
                self.vbus_lbl.configure(foreground='red')
            else:
                self.vbus_lbl.configure(foreground='black')
            self.vbus_lbl.configure(text=f'{v_b:0.3f}')

        if get_i:
            cur = dp.read_current()
            if cur < 1:
                self.i_lbl.configure(text=f'{cur*1000:0.0f}')
                self.i_mA_lbl.configure(text='mA')
            else:
                self.i_lbl.configure(text=f'{cur:0.3f}')
                self.i_mA_lbl.configure(text='A')

        if get_p:
            pwr = dp.read_power()
            if pwr/1000 < 1:
                self.p_lbl.configure(text=f'{pwr:0.0f}')
                self.p_mW_lbl.configure(text='mW')
            else:
                self.p_lbl.configure(text=f'{pwr/1e3:0.3f}')
                self.p_mW_lbl.configure(text='W')
            # calculate the value of the load resistance
            try:
                Rcalc = pwr*1e-3 / dp.read_current()**2
                self.rload_lbl.configure(text=f'{Rcalc:.1f}')
            except ZeroDivisionError:
                self.rload_lbl.configure(text='---')
                print('current is 0. Division by 0')
                return


    def test_func(self):
        OPT = True
        if OPT:
            vals = dp.read_registers()
            self.test_lbl.configure(text=vals)
        else:
            Rcalc = dp.read_power()*1e-3 / dp.read_current()**2
            self.test_lbl.configure(text=f'{Rcalc:.1f} Ohm')


class ConfigFrame(ttk.Frame):

    global dp

    def __init__(self, parent=None, DEBUG=False):
        super().__init__(parent)

        # 'self' in this context is ttk.Frame, so we can configure it
        # ! self.configure(bg='transparent')
        self.place(relx=0.05, rely=0.1, relwidth=.8, relheight=.8)
        # self.pack(expand=True, fill='both')

        self.DEBUG = DEBUG
        self.comm = None
        self.ent_focus_colors = None
        self.chk_var = tk.IntVar()
        self.adc_conv_time = ['72us', '132us', '258us', '508us', '1.01ms',
                              '2.01ms', '4.01ms', '8.01ms', '16.01ms', '32.01ms', '64.01ms']
        self.bus_vrange = ['16V', '32V', '60V']
        self.sh_vrange = ['40mV', '80mV', '160mV', '320mV']
        self.adc_conv_mode = ['Power-down', 'Shunt voltage (trig)',
                              'Bus voltge (trig)', 'Shunt and Bus (trig)',
                              'ADC off (disabled)', 'Shunt voltage (cont)',
                              'Bus voltge (cont)', 'Shunt and Bus (cont)']

        # *** THIS MUST BE THE VERY LAST COMMAND if we are to use the params defined above ***
        self.buildFrame()

    def buildFrame(self):

        # create a Frame inside Configuration Tab for easy manipulation (placement, size changes etc)
        cfgFrm = ttk.Frame(self)
        cfgFrm.place(relx=0.0, rely=0, relwidth=1, relheight=1)

        # create and place column headers
        ttk.Label(cfgFrm, text='Conversion Time', font=('Helvetica', 11)).grid(row=0, column=1, padx=20, pady=5, sticky='we')
        ttk.Label(cfgFrm, text='Range', font=('Helvetica', 11)).grid(row=0, column=2, padx=20, pady=5, sticky='we')

        # create and place column 0 labels: titles
        ttk.Label(cfgFrm, text='Vbus', font=('Helvetica', 10)).grid(row=1, column=0, padx=5, pady=10, sticky='e')
        ttk.Label(cfgFrm, text='Vshunt', font=('Helvetica', 10)).grid(row=2, column=0, padx=5, pady=10, sticky='e')
        ttk.Label(cfgFrm, text='Mode', font=('Helvetica', 10)).grid(row=3, column=0, padx=5, pady=10, sticky='e')
        ttk.Label(cfgFrm, text='Rshunt Value (Ohm)', font=('Helvetica bold', 10)).grid(row=4, column=0, padx=5, pady=10, sticky='e')
        ttk.Label(cfgFrm, text='Configuration Reg', font=('Helvetica', 10)).grid(row=5, column=0, padx=5, pady=10, sticky='e')
        ttk.Label(cfgFrm, text='Calibration Reg', font=('Helvetica', 10)).grid(row=6, column=0, padx=5, pady=10, sticky='e')

        # create combo boxes: selecting DPM paramters for Configuration and Calibration Registers
        self.bus_conv_time_cb = ttk.Combobox(cfgFrm, values=self.adc_conv_time, font=('Helvetica', 10))
        self.bus_vrange_cb = ttk.Combobox(cfgFrm, values=self.bus_vrange, font=('Helvetica', 10))
        self.sh_conv_time_cb = ttk.Combobox(cfgFrm, values=self.adc_conv_time, font=('Helvetica', 10))
        self.sh_vrange_cb = ttk.Combobox(cfgFrm, values=self.sh_vrange, font=('Helvetica', 10))
        self.conv_mode_cb = ttk.Combobox(cfgFrm, values=self.adc_conv_mode, font=('Helvetica', 10))
        self.ent_rshunt = ttk.Label(cfgFrm, text=dp.rshunt, anchor='w', font=('Helvetica', 11), takefocus=True)
        self.cfg_reg_lbl = ttk.Label(cfgFrm, text='', anchor='w', font=('Helvetica', 11))
        self.cal_reg_lbl = ttk.Label(cfgFrm, text='calib', anchor='w', font=('Helvetica', 11))

        # place the combo/entry boxes on the screen
        self.bus_conv_time_cb.grid(row=1, column=1, padx=20, sticky='e')
        self.bus_vrange_cb.grid(row=1, column=2, padx=20, sticky='e')
        self.sh_conv_time_cb.grid(row=2, column=1, padx=20, sticky='e')
        self.sh_vrange_cb.grid(row=2, column=2, padx=20, sticky='e')
        self.conv_mode_cb.grid(row=3, column=1, columnspan=2, padx=20, pady=10, sticky='we')
        self.ent_rshunt.grid(row=4, column=1, columnspan=2, padx=20, pady=10, sticky='we')
        self.cfg_reg_lbl.grid(row=5, column=1, padx=20, pady=2, sticky='we', columnspan=2)
        self.cal_reg_lbl.grid(row=6, column=1, padx=20, pady=2, sticky='we', columnspan=2)

        # initialize values inside the combo/entry boxes
        self.bus_conv_time_cb.set(self.adc_conv_time[3])
        self.bus_vrange_cb.set(self.bus_vrange[1])
        self.sh_conv_time_cb.set(self.adc_conv_time[2])
        self.sh_vrange_cb.set(self.sh_vrange[0])
        self.conv_mode_cb.set(self.adc_conv_mode[7])

        self.set_config_reg_label()  # calculate and display the value of Configuration Register
        self.set_calib_reg_label()  # calculate and display the value of Calibration Register

        if self.DEBUG:
            self.test_btn = ttk.Button(configFrm, text='Read test', width=10, command=self.testRead)
            self.test_lbl = ttk.Label(configFrm, text="debug message", anchor='w')

            self.test_btn.grid(row=7, column=0, padx=5, pady=5)
            self.test_lbl.grid(row=7, column=1, padx=5, pady=5, sticky='we', columnspan=2)
            # self.test_lbl.configure(width=40)

        # When the Rshunt box gets focus and the <Return> key was pressed or mouse-click open a new dialog
        self.ent_rshunt.bind('<FocusIn>', self.entry_lbl_focus_in)  # change appearnace when ready for editing
        self.ent_rshunt.bind('<FocusOut>', self.entry_lbl_focus_out)  # change appearnace back to original when done
        self.ent_rshunt.bind('<Return>', self.validate_rshunt_val)  # detect the Return button, so pop-up the dialog
        self.ent_rshunt.bind('<Button-1>', self.validate_rshunt_val)  # detect a mouse click on lable to pop-up the dialog

        # When an item in any of the combo boxes is selected call the callback function to process
        self.bus_vrange_cb.bind('<<ComboboxSelected>>', self.get_combo_selection)
        self.sh_vrange_cb.bind('<<ComboboxSelected>>', self.get_combo_selection)
        self.bus_conv_time_cb.bind('<<ComboboxSelected>>', self.get_combo_selection)
        self.sh_conv_time_cb.bind('<<ComboboxSelected>>', self.get_combo_selection)
        self.conv_mode_cb.bind('<<ComboboxSelected>>', self.get_combo_selection)

    def get_combo_selection(self, event):
        '''When an element in the combo box was selected get the index of all combo boxes and save them as\
            dp attributes. Based on the values, calculate the register value and present it in binary and hex\
            Finally, apply the selections to the Measurement window'''
        dp.brng = self.bus_vrange.index(self.bus_vrange_cb.get())
        dp.pg = self.sh_vrange.index(self.sh_vrange_cb.get())
        dp.badc = self.adc_conv_time.index(self.bus_conv_time_cb.get())
        dp.sadc = self.adc_conv_time.index(self.sh_conv_time_cb.get())
        dp.mode = self.adc_conv_mode.index(self.conv_mode_cb.get())
        # print(dp.brng, dp.pg, dp.badc, dp.sadc, dp.mode)
        self.set_config_reg_label()
        self.set_calib_reg_label()
        self.apply_dpm_config()

    def entry_lbl_focus_in(self, event):
        self.ent_focus_colors = self.ent_rshunt.cget('background')  # Try background, border color/width, etc.
        self.ent_rshunt.configure(background='#99ccff')

    def entry_lbl_focus_out(self, event):
        self.ent_rshunt.configure(background=self.ent_focus_colors)

    def validate_rshunt_val(self, event):
        # check if 'OK' or 'Cancel' was pressed
        if inp := simpledialog.askfloat('Enter Rshunt Value','Are you sure you want to change Rshunt value?\n \
                If yes, verify the value on the board \n \
                and enter as a floating point number'):
            # If 'OK' was pressed, update the combo box
            dp.rshunt = inp
            self.ent_rshunt.configure(text=dp.rshunt)
            self.ent_rshunt.tk_focusNext().focus()  # Must move focus next widget
            self.apply_dpm_config()
        self.ent_rshunt.tk_focusNext().focus()  # Must move focus next, otherwise cannot move on in case of 'Cancel"

    def set_config_reg_label(self):
        """Calculates the Configuration Register value based on individual parts
            Displays the calculated value in binary and hex format"""
        bit = f'0 {dp.brng:02b} {dp.pg:02b} {dp.badc:04b} {dp.sadc:04b} {dp.mode:03b}'
        word = (dp.brng << 13) | (dp.pg << 11) | (dp.badc << 7) | (dp.sadc << 3) | dp.mode
        lbl_text = bit + f' [{word:04X} hex]'
        self.cfg_reg_lbl.configure(text=lbl_text)

    def set_calib_reg_label(self):
        """Calculates the Calibration Register value based on individual parts
            Displays the calculated value in binary and hex format"""

        vshuntfs = dp.vshunt_range_tbl[dp.pg]
        word = int(1342.177 / vshuntfs)
        lbl_text = f'{word:>016b}   [{word:4X} hex]'
        self.cal_reg_lbl.configure(text=lbl_text)

    def apply_dpm_config(self):
        """When a new selection was made on the Configuration Tab, update the appearance of the fields\
            in the measurement window"""
        measFrm.meas_in_progress = False
        measFrm.btn_start_meas.configure(text='START')

        # Actions to do depending on the value of the MODE BITS
        if dp.mode == 0 or dp.mode == 4:
            # Power Down, ADC OFF
            measFrm.vshunt_lbl.configure(text='---', state='disabled')
            measFrm.vbus_lbl.configure(text='---', state='disabled')
            measFrm.i_lbl.configure(text='---', state='disabled')
            measFrm.p_lbl.configure(text='---', state='disabled')
            measFrm.rload_lbl.configure(text='---', state='disabled')

        elif dp.mode == 1 or dp.mode == 5:
            measFrm.vshunt_lbl.configure(text='---', state='normal')
            measFrm.vbus_lbl.configure(text='---', state='disabled')
            measFrm.i_lbl.configure(text='---', state='normal')
            measFrm.p_lbl.configure(text='---', state='disabled')
            measFrm.rload_lbl.configure(text='---', state='disabled')

        elif dp.mode == 2 or dp.mode == 6:
            measFrm.vshunt_lbl.configure(text='---', state='disabled')
            measFrm.vbus_lbl.configure(text='---', state='normal')
            measFrm.i_lbl.configure(text='---', state='disabled')
            measFrm.p_lbl.configure(text='---', state='disabled')
            measFrm.rload_lbl.configure(text='---', state='disabled')

        else:
            measFrm.vshunt_lbl.configure(text='---', state='normal')
            measFrm.vbus_lbl.configure(text='---', state='normal')
            measFrm.i_lbl.configure(text='---', state='normal')
            measFrm.p_lbl.configure(text='---', state='normal')
            measFrm.rload_lbl.configure(text='---', state='normal')

        dp.prog_config_reg()  # programs the DPM Configuration Register
        dp.prog_calib_reg()  # programs the DPM Calibration Register

    def testRead(self):
        # displays the values of configuration Tab in this label
        vals = f'brng={dp.brng} pg={dp.pg} badc={dp.badc} sadc={dp.sadc} mode={dp.mode} rval={dp.rshunt}'
        self.test_lbl.configure(text=vals)


if __name__ == "__main__":

    app = App('Digital Power Monitoring (DPM) Dashboard App', (680, 440))

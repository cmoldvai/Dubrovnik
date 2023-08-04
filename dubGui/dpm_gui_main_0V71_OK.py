import os
import json
# from tkinter.messagebox import showerror
# from tkinter import messagebox
from tkinter import simpledialog
from tkinter.messagebox import showerror, showinfo
# import tkinter as tk
# from tkinter import ttk
import customtkinter as ctk
from tkinter import Menu

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


class App(ctk.CTk):
    def __init__(self, title, size):
        super().__init__()

        global dp
        self.title(title)
        if MEAS_TAB_DBG:
            self.geometry(f'{size[0]}x{size[1]+30}')
        else:
            self.geometry(f'{size[0]}x{size[1]}')

        self.minsize(size[0], size[1])
        # self.resizable(False,False)

        ctk.set_appearance_mode("system")  # options are: 'system','dark','light'
        ctk.set_default_color_theme("dark-blue")  # Themes: "blue" (standard), "green", "dark-blue"

        cm = boardcom.BoardComm()   # create an instance of class Comm
        dp = dpm.DpmEK(cm)         # create an instance of class DpmEK

        portList = cm.findPorts()

    # ******************************************
    # ******             TABS           ********
    # ******************************************
        tabs = ctk.CTkTabview(self, width=size[0], height=size[1])
        tab1 = tabs.add('Measurements')
        tab2 = tabs.add('DPM Configuration')
        tab3 = tabs.add('Connection')
        # tabs.grid(row=0, column=0, columnspan=3, padx=10, pady=5, sticky='')
        # tabs.grid(padx=10, pady=5, sticky='nswe')
        # tabs.pack(side='top', expand=True, fill='x')
        #! USE 'place' !!!!!!! This will ensure the status bar goes on bottom
        #! TABS and STATUS BAR are all children of the main App()
        tabs.place(x=0,y=0,relheight=.9,relwidth=1)

    # *******************************************
    # ****** Serial Communications Tab ********
    # *******************************************
        global comFrm

        comFrm = SerComFrame(tab3, DEBUG=SERCOM_DBG)  # invoking the class
        #! Fix frame locations in customTkinter
        # ydim = 280
        # if SERCOM_DBG:
        #     comFrm.configure(width=size[0]-40, height=ydim+40, border_width=4)
        # else:
        #     comFrm.configure(width=size[0]-40, height=ydim, border_width=2)
        # comFrm.grid(row=1, column=0, padx=10, pady=4, sticky='nw')
        
        
        comFrm.combo.set(portList[0])
        comFrm.comm = cm

    # *******************************
    # ****** Measurement Tab ********
    # *******************************
        global measFrm
        measFrm = MeasurementFrame(tab1, DEBUG=MEAS_TAB_DBG)  # invoking the class

        # ydim = 280
        # if MEAS_TAB_DBG:
        #     measFrm.configure(width=580, height=ydim+40, border_width=4)
        # else:
        #     measFrm.configure(width=580, height=ydim, border_width=2)
        # measFrm.grid(row=2, column=0, padx=10, pady=4, sticky='nw')

        measFrm.comm = cm   # initializeing self.com in DpmMain class

    # ******************************
    # ****** DPM Config Tab ********
    # ******************************
        global configFrm

        configFrm = ConfigFrame(tab2, DEBUG=CFG_TAB_DBG)  # invoking the class

        # y_cF = 300
        # if CFG_TAB_DBG:
        #     configFrm.configure(width=580, height=y_cF+40, border_width=4)
        # else:
        #     configFrm.configure(width=580, height=y_cF, border_width=2)
        # configFrm.grid(row=2, column=0, padx=10, pady=4, sticky='nw')

        configFrm.comm = cm   # initializeing self.com in DpmMain class

    # ***************************
    # ****** Status Bar *********
    # ***************************
        global stsBar

        #! USE 'place' !!!!!!! This will ensure the status bar goes on bottom
        #! TABS and STATUS BAR are all children of the main App()

        stsFrm = ctk.CTkFrame(self, fg_color='transparent')
        stsFrm.place(relx=0,rely=0.9,relheight=.1,relwidth=1)

        #! DELETE THIS ONCE STABLE (need to incorporate DEBUG window size)
        # stsFrm.pack(side='bottom', expand=True, fill='x',padx=10, pady=10)
        # stsFrm.grid(row=3, column=0, columnspan=3,
        #             sticky='nsew', padx=5, pady=5)

        stsBar = ctk.CTkLabel(stsFrm, text='Not connected', anchor='w', font=('Helvetica', 14))
        stsBar.pack(side='bottom', expand=True, fill='both', ipadx=5, ipady=2, padx=10)

        # ********** MENU ***********
        my_menu = Menu(self) #! was tk.Menu find a way to add a CTk Menu
        self.configure(menu=my_menu)

        config_menu = Menu(my_menu, tearoff=False) #! was tk.Menu find a way to add a CTk Menu
        my_menu.add_cascade(label="Config", menu=config_menu)
        config_menu.add_command(label="Load config", command=comFrm.loadConfig)
        config_menu.add_command(label="Store config",
                                command=comFrm.saveConfig)
        config_menu.add_command(label="Restore defaults",
                                command=comFrm.loadDefaultSettings)

        help_menu = Menu(my_menu, tearoff=False) #! was tk.Menu find a way to add a CTk Menu
        my_menu.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="Help")
        help_menu.add_separator()
        help_menu.add_command(label="About", command=self.showAbout)

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

    def showAbout(self):
        aboutMsg = '''
        *************************
        *** DPM EVK Dashboard ***
        *************************

        Ver 0.96
        Requires updated dpm.py with changed function names (prog_ instead of set_)
        Authors:
        Csaba Moldvai, Eyal Barzilay
        '''
        showinfo('About', aboutMsg)


class SerComFrame(ctk.CTkFrame):

    global comFrm  # ! Check global
    global dp

    def __init__(self, parent=None, DEBUG=False):
        super().__init__(parent)

        # 'self' in this context is CTkFrame, so we can configure it
        self.configure(fg_color='transparent')
        self.place(x=0,y=0,relwidth=1,relheight=.8)

        self.DEBUG = DEBUG
        self.STANDALONE = False
        self.comm = None   # object created by boardcom
        self.portStatus = 'disconnected'
        self.selPort = ''  # keeps track of the selected port, between calls
        self.lastUsedPort = None
        self.portList = []
        self.portHandle = None
        self.chk_var = ctk.IntVar()
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
        #! Check why it doesn't behave
        comFrm = ctk.CTkFrame(self)
        comFrm.place(relx=0.01, rely=0.1, relwidth=1, relheight=.8)
        # comFrm.pack(expand=True, fill='both')
        comFrm.columnconfigure((0, 1, 2), weight=1)

        chk = ctk.CTkCheckBox(comFrm, text='Auto connect', variable=self.chk_var, font=('Helvetica', 14))
        self.combo = ctk.CTkComboBox(comFrm, values=self.portList, command=self.updtPortList, font=('Helvetica', 14))
        self.btn2 = ctk.CTkButton(comFrm, text='Connect', command=self.connectPort, font=('Helvetica', 14))

        chk.grid(row=0, column=0, pady=20)
        self.combo.grid(row=0, column=1, padx=10, pady=20)
        self.btn2.grid(row=0, column=2, padx=10, pady=20)

        if self.STANDALONE:
            self.btn3 = ctk.CTkButton(comFrm, text='Save Config',command=self.saveConfig)
            self.btn3.grid(row=0, column=3, padx=10, sticky='e')

        if self.DEBUG:
            self.test_btn = ctk.CTkButton(comFrm, text='Testing', command=self.testSerComm)
            self.test_lbl = ctk.CTkLabel(comFrm, text="Debug message:", anchor='w', justify='left')
            
            self.test_btn.grid(row=1, column=0, padx=5, pady=10, columnspan=1)
            self.test_lbl.grid(row=1, column=1, padx=5, pady=10, sticky='we', columnspan=3)

    def updtPortList(self):
        self.portList = self.comm.findPorts()
        self.combo['values'] = self.portList
        self.combo.set(self.portList[0])

    def connectPort(self, defaultPort=None):
        if self.portStatus == 'disconnected':
            if defaultPort:
                self.selPort = defaultPort         # updates class variable as well
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
            self.btn2.configure(text='Connect') # update button label
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
        serParams = '%s, baud=%d, bytes=%1d,\nparity=%s, stop=%1d, protocol=%s' \
            % (self.comPort, self.comBaudrate, self.comBytesize, self.comParity, self.comStopbits, self.comXonXoff)
        self.test_lbl.configure(text=serParams)


class MeasurementFrame(ctk.CTkFrame):

    global dp

    def __init__(self, parent=None, DEBUG=False):
        super().__init__(parent)
        
        # 'self' in this context is CTkFrame, so we can configure it
        self.configure(fg_color='transparent')
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
        # measFrm = ctk.CTkFrame(self, fg_color='yellow', border_color='red', border_width=1)
        # btnFrm = ctk.CTkFrame(self, fg_color='transparent', border_color='red', border_width=1)
        measFrm = ctk.CTkFrame(self, fg_color='transparent')
        btnFrm = ctk.CTkFrame(self, fg_color='transparent')

        measFrm.place(relx=0, rely=0.1, relwidth=.6, relheight=.8)
        btnFrm.place(relx=0.6, rely=0.1, relwidth=.4, relheight=.8)

        # create the grid
        measFrm.rowconfigure((0, 1, 2, 3, 4), weight=1, uniform='a')
        measFrm.columnconfigure((0,2), weight=1)
        measFrm.columnconfigure(1, weight=2)

        # ROW 1. Labels for: shunt voltage, measurement value and unit
        ctk.CTkLabel(measFrm, text='Vshunt', font=('Helvetica', 14)).grid(row=0, column=0, padx=5, pady=5, sticky='e')
        self.vshunt_lbl = ctk.CTkLabel(measFrm, text="---", anchor='e',width=20, font=('Helvetica', 16))
        self.vshunt_lbl.grid(row=0, column=1, padx=5, pady=10, sticky='we')
        ctk.CTkLabel(measFrm, text='mV', font=('Helvetica', 14)).grid(row=0, column=2, padx=10, pady=5, sticky='w')

        # ROW 2. Labels for: bus voltage, measurement value  and unit
        ctk.CTkLabel(measFrm, text='Vbus', font=('Helvetica', 14)).grid(row=1, column=0, padx=5, pady=5, sticky='e')
        self.vbus_lbl = ctk.CTkLabel(measFrm, text="---", anchor='e', width=20, font=('Helvetica',16))
        self.vbus_lbl.grid(row=1, column=1, padx=5, pady=10, sticky='we')
        ctk.CTkLabel(measFrm, text='V', font=('Helvetica', 14)).grid(row=1, column=2, padx=10, pady=5, sticky='w')

        # ROW 3. Labels for: current, value and unit
        ctk.CTkLabel(measFrm, text='Current', font=('Helvetica', 14)).grid(row=2, column=0, padx=5, pady=5, sticky='e')
        self.i_lbl = ctk.CTkLabel(measFrm, text="---", anchor='e', width=20, font=('Helvetica',16))
        self.i_lbl.grid(row=2, column=1, padx=5, pady=10, sticky='we')
        self.i_mA_lbl = ctk.CTkLabel(measFrm, text='A', font=('Helvetica', 14))
        self.i_mA_lbl.grid(row=2, column=2, padx=10, pady=5, sticky='w')

        # ROW 4. Labels for: power, value and unit
        ctk.CTkLabel(measFrm, text='Power', font=('Helvetica', 14)).grid(row=3, column=0, padx=5, pady=5, sticky='e')
        self.p_lbl = ctk.CTkLabel(measFrm, text="---", anchor='e', width=20, font=('Helvetica',16))
        self.p_lbl.grid(row=3, column=1, padx=5, pady=10, sticky='we')
        self.p_mW_lbl = ctk.CTkLabel(measFrm, text='mW', font=('Helvetica', 14))
        self.p_mW_lbl.grid(row=3, column=2, padx=10, pady=5, sticky='w')

        # ROW 5. Labels for: calculated load resistance value and unit
        ctk.CTkLabel(measFrm, text='R load', font=('Helvetica', 14)).grid(row=4, column=0, padx=5, pady=5, sticky='e')
        self.rload_lbl = ctk.CTkLabel(measFrm, text="---", anchor='e', width=20, font=('Helvetica',16))
        self.rload_lbl.grid(row=4, column=1, padx=5, pady=10, sticky='we')
        ctk.CTkLabel(measFrm, text='Ohm', font=('Helvetica', 14)).grid(row=4, column=2, padx=10, pady=5, sticky='w')

        # Right side of the frame for the START/STOP button
        self.btn_start_meas = ctk.CTkButton(
            btnFrm, text='START', width=20, font=('Helvetica bold', 24), command=self.start_stop)
        self.btn_start_meas.pack(expand=True, padx=30, pady=10, ipadx=30, ipady=40)

        if self.DEBUG:
            self.test_btn = ctk.CTkButton(measFrm, text='Test Values', command=self.test_func)
            self.test_btn.grid(row=6, column=0, padx=5, pady=10, columnspan=1)
            self.test_lbl = ctk.CTkLabel(measFrm, text="debug message", anchor='w')
            self.test_lbl.grid(row=6, column=1, padx=5, pady=10, sticky='e', columnspan=3)
            # print parameters available for a tkinter Label
            # print(self.test_lbl.configure().keys())
            # self.test_lbl.configure(fg_color='#bbb')

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

        #! Not sure if this belongs here, but we need to initialize the chip after connecting (I guess)        
        dp.prog_calib_reg()   # Sometimes when starting the program we mesaure 0mA, 0mW, calib reg = 0x0

        if get_vs:
            v_sh = dp.read_shunt_voltage()
            if v_sh > dp.vshunt_range_tbl[dp.pg]:
                self.vshunt_lbl.configure(fg_color='yellow', width=20)
            else:
                self.vshunt_lbl.configure(fg_color='transparent', width=20)
            self.vshunt_lbl.configure(text=f'{1e3*v_sh:0.3f}')

        if get_vb:
            v_b = dp.read_bus_voltage()
            if v_b > dp.vbus_range_tbl[dp.brng]:
                self.vbus_lbl.configure(fg_color='yellow')
            else:
                self.vbus_lbl.configure(fg_color='transparent')
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
            vals = dp.readRegisters()
            self.test_lbl.configure(text=vals)
        else:
            Rcalc = dp.read_power()*1e-3 / dp.read_current()**2
            self.test_lbl.configure(text=f'{Rcalc:.1f} Ohm')


class ConfigFrame(ctk.CTkFrame):

    global dp

    def __init__(self, parent=None, DEBUG=False):
        super().__init__(parent)

        # 'self' in this context is CTkFrame, so we can configure it
        self.configure(fg_color='transparent')
        self.place(relx=0.1, rely=0.1, relwidth=.8, relheight=.8)
        # self.pack(expand=True, fill='both')

        self.DEBUG = DEBUG
        self.comm = None
        self.chk_var = ctk.IntVar()
        self.adc_conv_time = ['72us', '132us', '258us', '508us', '1.01ms',
                              '2.01ms', '4.01ms', '8.01ms', '16.01ms', '32.01ms', '64.01ms']
        self.bus_vrange = ['16V', '32V', '60V']
        self.sh_vrange = ['40mV', '80mV', '160mV', '320mV']
        self.adc_conv_mode = ['Power-down', 'Shunt voltage (trig)',
                              'Bus voltge (trig)', 'Shunt and Bus (trig)',
                              'ADC off (disabled)', 'Shunt voltage (cont)',
                              'Bus voltge (cont)', 'Shunt and Bus (cont)']

        self.myComboBoxSelection = ctk.StringVar()  #! This is to deal with ComboBox selection issue

        # *** THIS MUST BE THE VERY LAST COMMAND if we are to use the params defined above ***
        self.buildFrame()

    def buildFrame(self):

        configFrm = ctk.CTkFrame(self)
        configFrm.place(relx=0.0, rely=0, relwidth=1, relheight=1)
        # configFrm.place(relx=0.01, rely=0.1, relwidth=.98, relheight=.8)

        # lblFrm = ttk.Frame(self)
        # lblFrm.place(relx=0.7, rely=0.05, relwidth=.3, relheight=1)
        # ctk.CTkLabel(lblFrm, text='TEST', fg_color='red').pack(expand=True, fill='both')

        ctk.CTkLabel(configFrm, text='Conversion Time', font=('Helvetica', 16)).grid(
            row=0, column=1, padx=20, pady=5, sticky='we')

        ctk.CTkLabel(configFrm, text='Range', font=('Helvetica', 16)).grid(
            row=0, column=2, padx=20, pady=5, sticky='we')

        ctk.CTkLabel(configFrm, text='Vbus', font=('Helvetica', 14)).grid(
            row=1, column=0, padx=5, pady=10, sticky='e')

        ctk.CTkLabel(configFrm, text='Vshunt', font=('Helvetica', 14)).grid(
            row=2, column=0, padx=5, pady=10, sticky='e')

        ctk.CTkLabel(configFrm, text='Mode', font=('Helvetica', 14)).grid(
            row=3, column=0, padx=5, pady=10, sticky='e')

        self.bus_conv_time_cb = ctk.CTkComboBox(configFrm, values=self.adc_conv_time, command=self.get_combo_selection, font=('Helvetica', 14))
        self.bus_conv_time_cb.grid(row=1, column=1, padx=20, sticky='e')
        self.bus_conv_time_cb.set(self.adc_conv_time[3])

        self.bus_vrange_cb = ctk.CTkComboBox(configFrm, values=self.bus_vrange, command=self.get_combo_selection, font=('Helvetica', 14))
        self.bus_vrange_cb.grid(row=1, column=2, padx=20, sticky='e')
        self.bus_vrange_cb.set(self.bus_vrange[1])

        self.sh_conv_time_cb = ctk.CTkComboBox(configFrm, values=self.adc_conv_time, command=self.get_combo_selection, font=('Helvetica', 14))
        self.sh_conv_time_cb.grid(row=2, column=1, padx=20, sticky='e')
        self.sh_conv_time_cb.set(self.adc_conv_time[2])

        self.sh_vrange_cb = ctk.CTkComboBox(configFrm, values=self.sh_vrange, command=self.get_combo_selection, font=('Helvetica', 14))
        self.sh_vrange_cb.grid(row=2, column=2, padx=20, sticky='e')
        self.sh_vrange_cb.set(self.sh_vrange[0])

        self.conv_mode_cb = ctk.CTkComboBox(configFrm, values=self.adc_conv_mode, command=self.get_combo_selection, font=('Helvetica', 14))
        self.conv_mode_cb.grid(row=3, column=1, columnspan=2, padx=20, pady=10, sticky='we')
        self.conv_mode_cb.set(self.adc_conv_mode[7])

        ctk.CTkLabel(configFrm, text='Rshunt Value (Ohm)', font=('Helvetica', 14)).grid(
            row=4, column=0, padx=5, pady=10, sticky='e')
        self.ent_rshunt = ctk.CTkLabel(configFrm, text=dp.rshunt, anchor='center', takefocus=True, font=('Helvetica', 16))
        self.ent_rshunt.grid(row=4, column=1, columnspan=2,
                             padx=20, pady=10, sticky='we')

        ctk.CTkLabel(configFrm, text='Config Reg', font=('Helvetica', 14)).grid(row=5, column=0, padx=5, pady=10, sticky='e')
        self.cfg_reg_lbl = ctk.CTkLabel(configFrm, text='', anchor='center', font=('Helvetica', 16))
        self.cfg_reg_lbl.grid(row=5, column=1, padx=20, pady=5, sticky='we', columnspan=2)

        self.set_config_reg_label()

        if self.DEBUG:
            self.test_btn = ctk.CTkButton(configFrm, text='Read test', width=10, command=self.testRead)
            self.test_lbl = ctk.CTkLabel(configFrm, text="debug message", anchor='w')

            self.test_btn.grid(row=7, column=0, padx=5, pady=5)
            self.test_lbl.grid(row=7, column=1, padx=5, pady=5, sticky='we', columnspan=2)
            # self.test_lbl.configure(width=40)

        # When the label gets focus and the <Return> key was pressed or mouse-click open a new dialog
        self.ent_rshunt.bind('<FocusIn>', self.entry_lbl_focus_in)  # change appearnace when ready for editing
        self.ent_rshunt.bind('<FocusOut>', self.entry_lbl_focus_out) # change appearnace back to original when done
        self.ent_rshunt.bind('<Return>', self.validate_rshunt_val)  # detect the Return button, so pop-up the dialog
        self.ent_rshunt.bind('<Button-1>', self.validate_rshunt_val)  # detect a mouse click on lable to pop-up the dialog

        # When an item in the combo box selected call a function 
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
        self.apply_dpm_config()

    def entry_lbl_focus_in(self, event):
        self.ent_focus_colors = self.ent_rshunt.cget('fg_color')  # Try background, border color/width, etc.
        self.ent_rshunt.configure(fg_color='#99ccff')

    def entry_lbl_focus_out(self, event):
        self.ent_rshunt.configure(fg_color=self.ent_focus_colors)
    
    def validate_rshunt_val(self, event):
        # check if 'OK' or 'Cancel' was pressed
        if inp := simpledialog.askfloat('Enter Rshunt Value','Are you sure you want to change Rshunt value?\n \
                If yes, verify the value on the board \n \
                and enter as a floating point number'):
            # If 'OK' was pressed, update the combo box
            dp.rshunt = inp
            # self.ent_rshunt['text'] = f'{dp.rshunt} Ohm'
            self.ent_rshunt.configure(text=dp.rshunt)
            # self.ent_rshunt['text'] = dp.rshunt
            self.ent_rshunt.tk_focusNext().focus()  # Must move focus next widget
            self.apply_dpm_config()
        self.ent_rshunt.tk_focusNext().focus()  # Must move focus next, otherwise cannot move on in case of 'Cancel"

    def set_config_reg_label(self):
        """Calculates the Configuration Register value based on individual parts
            Displays the calculated value in binary and hex format"""
        b = f'0 {dp.brng:02b} {dp.pg:02b} {dp.badc:04b} {dp.sadc:04b} {dp.mode:03b}'
        w = (dp.brng << 13) | (dp.pg << 11) | (
            dp.badc << 7) | (dp.sadc << 3) | dp.mode
        lbl_text = b + f' [{w:04X} hex]'
        self.cfg_reg_lbl.configure(text=lbl_text)

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

    app = App('Digital Power Monitoring (DPM) Dashboard App', (680, 500))

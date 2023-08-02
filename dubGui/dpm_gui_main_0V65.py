import os
import json
# from tkinter.messagebox import showerror
# from tkinter import messagebox
from tkinter import simpledialog
from tkinter.messagebox import showerror, showinfo
# from tkinter import *
import tkinter as tk
from tkinter import ttk
from dubLibs import boardcom
from dubLibs import dpm

SERCOM_DBG = False
MEAS_TAB_DBG = False
CFG_TAB_DBG = True

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
        self.geometry(f'{size[0]}x{size[1]}')
        # self.minsize(size[0], size[1])
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
        tabs.grid(row=0, column=0, columnspan=3, padx=10, pady=5, sticky='')

    # *******************************************
    # ****** Serial Communications Tab ********
    # *******************************************
        global comFrm

        comFrm = SerComFrame(tab3, DEBUG=SERCOM_DBG)  # invoking the class
        serComFrm_height = 60
        if SERCOM_DBG:
            comFrm.config(width=350, height=serComFrm_height +
                          40, borderwidth=4, relief='groove')
        else:
            comFrm.config(width=350, height=serComFrm_height,
                          borderwidth=2, relief='flat')
        comFrm.grid(row=1, column=0, padx=10, pady=4, sticky='nw')
        comFrm.combo.set(portList[0])
        comFrm.comm = cm

    # *******************************
    # ****** Measurement Tab ********
    # *******************************
        global measFrm
        measFrm = MeasurementFrame(
            tab1, DEBUG=MEAS_TAB_DBG)  # invoking the class
        ydim = 280
        if MEAS_TAB_DBG:
            measFrm.config(width=580, height=ydim+40,
                           borderwidth=4, relief='ridge')
        else:
            measFrm.config(width=580, height=ydim,
                           borderwidth=2, relief='flat')
        measFrm.grid(row=2, column=0, padx=10, pady=4, sticky='nw')
        measFrm.comm = cm   # initializeing self.com in DpmMain class

    # ******************************
    # ****** DPM Config Tab ********
    # ******************************
        global configFrm

        configFrm = ConfigFrame(tab2, DEBUG=CFG_TAB_DBG)  # invoking the class
        y_cF = 300
        if CFG_TAB_DBG:
            configFrm.config(width=580, height=y_cF +
                             40, borderwidth=4, relief='ridge')
        else:
            configFrm.config(width=580, height=y_cF,
                             borderwidth=2, relief='flat')
        configFrm.grid(row=2, column=0, padx=10, pady=4, sticky='nw')
        configFrm.comm = cm   # initializeing self.com in DpmMain class

    # ***************************
    # ****** Status Bar *********
    # ***************************
        global stsBar

        stsFrm = ttk.Frame(self)
        stsFrm.grid(row=3, column=0, columnspan=3,
                    sticky='nsew', padx=5, pady=5)

        stsBar = ttk.Label(
            stsFrm, text='Not connected', font=("Helvetica", 9), anchor='w', relief='sunken')
        stsBar.pack(side='bottom', expand=True, fill='both', ipadx=5, ipady=2)

        # ********** MENU ***********
        my_menu = tk.Menu(self)
        self.config(menu=my_menu)

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

        stsBar.config(text=comFrm.serParams)

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

        Ver 0.8
        Authors:
        Csaba Moldvai, Eyal Barzilay
        '''
        showinfo('About', aboutMsg)


class SerComFrame(ttk.Frame):

    global comFrm  # ! Check global
    global dp

    def __init__(self, parent=None, DEBUG=False):
        ttk.Frame.__init__(self, parent)
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
        '''Makes a reusable frame for a connecting to Dubrovnik board'''
        chk = ttk.Checkbutton(self, text='Auto connect', variable=self.chk_var)
        chk.grid(row=0, column=0)

        self.combo = ttk.Combobox(
            self, width=10, values=self.portList, postcommand=self.updtPortList)
        self.combo.grid(row=0, column=1, padx=10)

        self.btn2 = ttk.Button(self, text='Connect', width=10,
                               command=self.connectPort)
        self.btn2.grid(row=0, column=2, padx=10)

        if self.STANDALONE:
            self.btn3 = ttk.Button(self, text='Save Config', width=10,
                                   command=self.saveConfig)
            self.btn3.grid(row=0, column=3, padx=10, sticky='e')

        if self.DEBUG:
            self.test_btn = ttk.Button(self, text='Testing',
                                       width=10, command=self.testSerComm)
            self.test_btn.grid(row=1, column=0, padx=5, pady=10, columnspan=1)
            self.test_lbl = ttk.Label(
                self, text="Debug message:", anchor='w', justify='left')
            self.test_lbl.grid(row=1, column=1, padx=5,
                               pady=10, sticky='we', columnspan=3)

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
            self.btn2.config(text='Disconnect')  # change button label
            self.portStatus = 'connected'  # update connection status
            self.serParams = f'Connected: {self.comPort} ({self.comBaudrate},{self.comBytesize},{self.comParity},{self.comStopbits},{self.comXonXoff})'
            stsBar.config(text=self.serParams)

        elif self.portStatus == 'connected':
            # if connected, disconnect from the current port
            self.disconnectPort(self.selPort)
            self.btn2['text'] = 'Connect'  # update button label
            self.portStatus = 'disconnected'  # update connection status
            stsBar.config(text='Disconnected')
        else:
            print('No such port. Try again!!!')
        self.saveConfig()

    def disconnectPort(self, selPort):
        self.comm.disconnect(selPort)
        # print(f"Port: {selPort} disconnected")
        stsBar.config(text='No COM port found!')

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
        configFrm.bus_vrange_cb.set(configFrm.bus_vrange[dp.brng])
        configFrm.sh_vrange_cb.set(configFrm.sh_vrange[dp.pg])
        configFrm.bus_conv_time_cb.set(configFrm.adc_conv_time[dp.badc])
        configFrm.sh_conv_time_cb.set(configFrm.adc_conv_time[dp.sadc])
        configFrm.conv_mode_cb.set(configFrm.adc_conv_mode[dp.mode])
        # configFrm.rshunt_var.set(dp.rshunt)
   
    def testSerComm(self):
        serParams = '%s, baud=%d, bytes=%1d,\nparity=%s, stop=%1d, protocol=%s' \
            % (self.comPort, self.comBaudrate, self.comBytesize, self.comParity, self.comStopbits, self.comXonXoff)
        self.test_lbl.config(text=serParams)


class MeasurementFrame(ttk.Frame):

    global dp

    def __init__(self, parent=None, DEBUG=False):
        # tk.LabelFrame.__init__(self, parent, padx=5, pady=5)
        ttk.Frame.__init__(self, parent)
        self.DEBUG = DEBUG
        self.comm = None
        self.meas_in_progress = False

        self.buildFrame()

    def buildFrame(self):
        # ROW 1. Labels for: shunt voltage, measurement value and unit
        ttk.Label(self, text='Vshunt').grid(
            row=0, column=0, padx=5, pady=5, sticky='e')
        self.vshunt_lbl = ttk.Label(self, text="0", relief='sunken', width=20,
                                    anchor='e', foreground='black', background='#f8f8f8', font=('Calibri', 12))
        self.vshunt_lbl.grid(row=0, column=1, padx=5, pady=10, sticky='we')
        ttk.Label(self, text='mV').grid(
            row=0, column=2, padx=10, pady=5, sticky='w')

        # ROW 2. Labels for: bus voltage, measurement value  and unit
        ttk.Label(self, text='Vbus').grid(
            row=1, column=0, padx=5, pady=5, sticky='e')

        self.vbus_lbl = ttk.Label(self, text="0", relief='sunken', width=20,
                                  anchor='e', foreground='black', background='#f8f8f8', font=('Calibri', 12))
        self.vbus_lbl.grid(row=1, column=1, padx=5,
                           pady=10, sticky='we')
        ttk.Label(self, text='V').grid(
            row=1, column=2, padx=10, pady=5, sticky='w')

        # ROW 3. Labels for: current, value and unit
        ttk.Label(self, text='Current').grid(
            row=2, column=0, padx=5, pady=5, sticky='e')
        self.i_lbl = ttk.Label(self, text="0", relief='sunken', width=20,
                               anchor='e', foreground='black', background='#f8f8f8', font=('Calibri', 12))
        self.i_lbl.grid(row=2, column=1, padx=5, pady=10, sticky='we')
        ttk.Label(self, text='A').grid(
            row=2, column=2, padx=10, pady=5, sticky='w')

        # ROW 4. Labels for: power, value and unit
        ttk.Label(self, text='Power').grid(
            row=3, column=0, padx=5, pady=5, sticky='e')
        self.p_lbl = ttk.Label(self, text="0", relief='sunken', width=20,
                               anchor='e', foreground='black', background='#f8f8f8', font=('Calibri', 12))
        self.p_lbl.grid(row=3, column=1, padx=5, pady=10, sticky='we')
        ttk.Label(self, text='mW').grid(
            row=3, column=2, padx=10, pady=5, sticky='w')

        self.btn_start_meas = ttk.Button(
            self, text='START', width=10, command=self.start_stop)  # removed font=('Calibri bold', 18),
        self.btn_start_meas.grid(
            row=4, column=1, padx=10, pady=10, sticky='we')

        if self.DEBUG:
            self.test_btn = ttk.Button(self, text='Reg Values',
                                       width=10, command=self.test_func)
            self.test_btn.grid(row=6, column=0, padx=5, pady=10, columnspan=1)
            self.test_lbl = ttk.Label(
                self, text="debug message", anchor='w', justify='center')
            self.test_lbl.grid(row=6, column=1, padx=5,
                               pady=10, sticky='we', columnspan=3)
            # Print parameters available for a Tkinter Label
            print(self.test_lbl.configure().keys())
            self.test_lbl.config(relief='sunken', background='#fff',
                                 width=40, font=('Calibri', 11))

    def start_stop(self):

        if dp.mode == 0 or dp.mode == 4:
            # Power Down, ADC Off
            self.get_a_measurement(0, 0, 0, 0)
            self.meas_in_progress = False
            self.btn_start_meas.config(text='START')

        elif dp.mode == 1:
            # Vshunt Triggered
            self.get_a_measurement(1, 0, 1, 0)
            self.meas_in_progress = False
            self.btn_start_meas.config(text='START')

        elif dp.mode == 2:
            # Vbus Triggered
            self.get_a_measurement(0, 1, 0, 0)
            self.meas_in_progress = False
            self.btn_start_meas.config(text='START')

        elif dp.mode == 3:
            # Vshunt+Vbus Triggered
            self.get_a_measurement(1, 1, 1, 1)
            self.meas_in_progress = False
            self.btn_start_meas.config(text='START')

        else:
            if not self.meas_in_progress:
                self.meas_in_progress = True
                self.btn_start_meas.config(
                    text='STOP')
                self.get_a_measurement(1, 1, 1, 1)
                self.update_measurement()
            else:
                self.meas_in_progress = False
                self.btn_start_meas.config(text='START')

    # Interrupt at periodic intervals
    def update_measurement(self):
        if self.meas_in_progress:
            self.get_a_measurement(1, 1, 1, 1)
            self.after(500, self.update_measurement)

    def get_a_measurement(self, get_vs, get_vb, get_i, get_p):
        dp.set_config()  # Clear CNVR Conversion Ready (Bit 1)

        if get_vs:
            v_sh = dp.read_shunt_voltage()
            if v_sh > dp.vshunt_range_tbl[dp.pg]:
                self.vshunt_lbl.config(foreground='red')
            else:
                self.vshunt_lbl.config(foreground='black')
            self.vshunt_lbl['text'] = f'{1e3*v_sh:0.3f}'

        if get_vb:
            v_b = dp.read_bus_voltage()
            if v_b > dp.vbus_range_tbl[dp.brng]:
                self.vbus_lbl.config(foreground='red')
            else:
                self.vbus_lbl.config(foreground='black')
            self.vbus_lbl['text'] = f'{v_b:0.3f}'

        if get_i:
            cur = dp.read_current()
            self.i_lbl.config(text=f'{cur:0.3f}')

        if get_p:
            pwr = dp.read_power()
            self.p_lbl.config(text=f'{pwr:0.3f}')

    def test_func(self):
        vals = dp.readRegisters()
        self.test_lbl.config(text=vals)


class ConfigFrame(ttk.Frame):

    global dp

    def __init__(self, parent=None, DEBUG=False):
        # tk.LabelFrame.__init__(self, parent, text='Configuration', padx=5, pady=5)
        ttk.Frame.__init__(self, parent)
        self.DEBUG = DEBUG
        self.comm = None
        # self.rshunt_var = tk.DoubleVar()  # used in Rshunt value entry box. Changed to a Label. Not needed
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
        # create widgets
        ttk.Label(self, text='Conv. Time').grid(
            row=0, column=1, padx=5, pady=5, sticky='we')

        ttk.Label(self, text='Range').grid(
            row=0, column=2, padx=5, pady=5, sticky='we')

        ttk.Label(self, text='Vbus').grid(
            row=1, column=0, padx=5, pady=5, sticky='e')

        ttk.Label(self, text='Vshunt').grid(
            row=2, column=0, padx=5, pady=5, sticky='e')

        ttk.Label(self, text='Mode').grid(
            row=3, column=0, padx=5, pady=5, sticky='e')

        self.bus_conv_time_cb = ttk.Combobox(
            self, width=8, values=self.adc_conv_time)
        self.bus_conv_time_cb.grid(row=1, column=1, padx=20, sticky='e')
        self.bus_conv_time_cb.set(self.adc_conv_time[3])

        self.bus_vrange_cb = ttk.Combobox(
            self, width=8, values=self.bus_vrange)
        self.bus_vrange_cb.grid(row=1, column=2, padx=20, sticky='e')
        self.bus_vrange_cb.set(self.bus_vrange[1])

        self.sh_conv_time_cb = ttk.Combobox(
            self, width=8, values=self.adc_conv_time)
        self.sh_conv_time_cb.grid(row=2, column=1, padx=20, sticky='e')
        self.sh_conv_time_cb.set(self.adc_conv_time[2])

        self.sh_vrange_cb = ttk.Combobox(
            self, width=8, values=self.sh_vrange)
        self.sh_vrange_cb.grid(row=2, column=2, padx=20, sticky='e')
        self.sh_vrange_cb.set(self.sh_vrange[0])

        self.conv_mode_cb = ttk.Combobox(
            self, width=8, values=self.adc_conv_mode)
        self.conv_mode_cb.grid(
            row=3, column=1, columnspan=2, padx=20, pady=10, sticky='we')
        self.conv_mode_cb.set(self.adc_conv_mode[7])

        ttk.Label(self, text='Rshunt Value').grid(
            row=4, column=0, padx=5, pady=5, sticky='e')
        self.ent_rshunt = ttk.Label(self, text=dp.rshunt, relief='sunken', background='#fff', anchor='e', takefocus=True)
        self.ent_rshunt.grid(row=4, column=1, columnspan=2,
                             padx=20, pady=10, sticky='we')
        ttk.Label(self, text='Ohm').grid(
            row=4, column=3, pady=5, sticky='w')
        # self.rshunt_var.set(dp.rshunt)

        ttk.Label(self, text='Config Reg').grid(
            row=5, column=0, padx=5, pady=5, sticky='e')
        self.cfg_reg_lbl = ttk.Label(self, text='', anchor='center')
        self.cfg_reg_lbl.grid(row=5, column=1, padx=20,
                              pady=5, sticky='we', columnspan=2)
        self.cfg_reg_lbl.config(
            relief='groove', width=28, font=('Calibri', 11))
        self.set_config_reg_label()  # TODO check if this is initialized in all cases

        if self.DEBUG:
            self.test_btn = ttk.Button(self, text='Read test',
                                       width=10, command=self.testRead)
            self.test_btn.grid(row=7, column=0, padx=5, pady=20, columnspan=1)
            self.test_lbl = ttk.Label(
                self, text="debug message", anchor='w')
            self.test_lbl.grid(row=7, column=1, padx=5,
                               pady=30, sticky='we', columnspan=3)
            self.test_lbl.config(relief='sunken', background='#fff',
                                 width=40, font=('Calibri', 10))

        # When any key pressed open a new dialog where the user can enter new Rshunt value
        # Tried <Return>, <FocusOut>, <KeyPress> and all have problems
        self.ent_rshunt.bind('<FocusIn>', self.entry_lbl_focus_in)  # capture event when the label got focus
        self.ent_rshunt.bind('<FocusOut>', self.entry_lbl_focus_out)  
        self.ent_rshunt.bind('<Return>', self.validate_rshunt_val)  # detect the Return button pressed event
        self.ent_rshunt.bind('<Button-1>', self.validate_rshunt_val)  # detect a mouse click inside the Entry box event. Open the dialog


        # When an item in the combo box selected call a function
        self.bus_vrange_cb.bind('<<ComboboxSelected>>', self.get_combo_selection)
        self.sh_vrange_cb.bind('<<ComboboxSelected>>', self.get_combo_selection)
        self.bus_conv_time_cb.bind('<<ComboboxSelected>>', self.get_combo_selection)
        self.sh_conv_time_cb.bind('<<ComboboxSelected>>', self.get_combo_selection)
        self.conv_mode_cb.bind('<<ComboboxSelected>>', self.get_combo_selection)

    def get_combo_selection(self, event):
        dp.brng = self.bus_vrange_cb.current()
        dp.pg = self.sh_vrange_cb.current()
        dp.badc = self.bus_conv_time_cb.current()
        dp.sadc = self.sh_conv_time_cb.current()
        dp.mode = self.conv_mode_cb.current()
        self.set_config_reg_label()
        self.apply_dpm_config()

    def entry_lbl_focus_in(self, event):
        self.ent_focus_colors = self.ent_rshunt.cget('background')  # Try background, border color/width, etc.
        self.ent_rshunt.config(background='#99ccff')

    def entry_lbl_focus_out(self, event):
        self.ent_rshunt.config(background=self.ent_focus_colors)
    
    def validate_rshunt_val(self, event):
        # check if 'OK' or 'Cancel' was pressed
        if inp := simpledialog.askfloat('Enter Rshunt Value','Are you sure you want to change Rshunt value?\n \
                If yes, verify the value on the board \n \
                and enter as a floating point number'):
            # If 'OK' was pressed, update the combo box
            dp.rshunt = inp
            self.ent_rshunt['text'] = dp.rshunt
            # self.rshunt_var.set(dp.rshunt)
            self.ent_rshunt.tk_focusNext().focus()  # Must move focus next widget

            self.apply_dpm_config()
        self.ent_rshunt.tk_focusNext().focus()  # Must move focus next, otherwise cannot move on in case of 'Cancel"

    def set_config_reg_label(self):
        b = f'0 {dp.brng:02b} {dp.pg:02b} {dp.badc:04b} {dp.sadc:04b} {dp.mode:03b}'
        w = (dp.brng << 13) | (dp.pg << 11) | (
            dp.badc << 7) | (dp.sadc << 3) | dp.mode
        lbl_text = b + f' = {w:04X}h'
        self.cfg_reg_lbl.config(text=lbl_text)

    def apply_dpm_config(self):

        #  TODO check this. Should it be here or in 'start_stop'?

        measFrm.meas_in_progress = False
        measFrm.btn_start_meas.config(text='START')
        # Actions to do depending on the value of the MODE BITS
        if dp.mode == 0 or dp.mode == 4:
            # Power Down, ADC OFF
            measFrm.vshunt_lbl.config(
                text='---', state='disabled', background='#e0e0e0')
            measFrm.vbus_lbl.config(
                text='---', state='disabled', background='#e0e0e0')
            measFrm.i_lbl.config(
                text='---', state='disabled', background='#e0e0e0')
            measFrm.p_lbl.config(
                text='---', state='disabled', background='#e0e0e0')

        elif dp.mode == 1 or dp.mode == 5:
            measFrm.vshunt_lbl.config(
                text='---', state='normal', background='#f8f8f8')
            measFrm.vbus_lbl.config(
                text='---', state='disabled', background='#e0e0e0')
            measFrm.i_lbl.config(text='---', state='normal',
                                 background='#f8f8f8')
            measFrm.p_lbl.config(
                text='---', state='disabled', background='#e0e0e0')

        elif dp.mode == 2 or dp.mode == 6:
            measFrm.vshunt_lbl.config(
                text='---', state='disabled', background='#e0e0e0')
            measFrm.vbus_lbl.config(
                text='---', state='normal', background='#f8f8f8')
            measFrm.i_lbl.config(
                text='---', state='disabled', background='#e0e0e0')
            measFrm.p_lbl.config(
                text='---', state='disabled', background='#e0e0e0')

        else:
            measFrm.vshunt_lbl.config(
                text='---', state='normal', background='#f8f8f8')
            measFrm.vbus_lbl.config(
                text='---', state='normal', background='#f8f8f8')
            measFrm.i_lbl.config(text='---', state='normal',
                                 background='#f8f8f8')
            measFrm.p_lbl.config(text='---', state='normal',
                                 background='#f8f8f8')

        # program DPM registers with values set in GUI
        # print(
        #     f'brng={dp.brng}, pg={dp.pg}, badc={dp.badc}, sadc={dp.sadc}, mode={dp.mode},rval={dp.rshunt}')
        dp.set_config()  # programs the DPM Configuration Register
        dp.set_calibration()  # programs the DPM Calibration Register

    def testRead(self):
        # displays the values of configuration Tab in this label
        vals = f'brng={dp.brng} pg={dp.pg} badc={dp.badc} sadc={dp.sadc} mode={dp.mode} rval={dp.rshunt}'
        self.test_lbl.config(text=vals)


if __name__ == "__main__":

    app = App('Digital Power Monitoring (DPM) Dashboard App', (600, 400))

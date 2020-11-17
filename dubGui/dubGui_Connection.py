import sys
import pickle
from tkinter import *
from tkinter import ttk
# from tkinter.messagebox import askretrycancel

class SerComInterface(Frame):

    def __init__(self, parent=None, DEBUG=False):
        LabelFrame.__init__(
            self, parent, text='Serial Connection', padx=5, pady=5)
        self.pack(side=TOP, anchor=NW, padx=10, pady=10)
        self.DEBUG = DEBUG
        self.comm = None                      # object created by boardcom
        self.portStatus = 'disconnected'
        self.selPort = ''  # ! keeps track of selected port, between calls
        self.portList = []
        self.chk_var = IntVar()
        self.autoConnect = 0
        with open('dubrovnik.pkl', 'rb') as fname:
            cfg = pickle.load(fname)
            print(cfg)
            self.autoConnect = cfg['autoConnect']
        self.chk_var.get()
        self.buildFrame()

    def buildFrame(self):
        '''Makes a reusable frame for a connecting to Dubrovnik board'''
        # self.chk_var = IntVar()
        chk = Checkbutton(self, text='Auto connect', variable=self.chk_var)
        chk.grid(row=0, column=0)
        self.chk_var.set(self.autoConnect)
        self.combo = ttk.Combobox(
            self, width=10, values=self.portList, postcommand=self.updtPortList)
        self.combo.grid(row=0, column=1, padx=10)
        # self.combo.current(0)
        self.btn2 = Button(self, width=12, text='Connect',
                           command=self.connectPort)
        self.btn2.grid(row=0, column=2, padx=10)
        self.btn3 = Button(self, text='Save Config',
                                command=self.saveConfig)
        self.btn3.grid(row=0, column=3, padx=10, sticky=E)

        if self.DEBUG:
            self.test_btn1 = Button(self, text='Testing', command=self.testing)
            self.test_btn1.grid(row=3, column=1, sticky=S)

            self.test_lbl = Label(self, text='debug messages')
            self.test_lbl.grid(row=4, column=1, sticky=S)

    def updtPortList(self):
        self.portList = self.comm.findPorts()
        self.combo['values'] = self.portList
        self.combo.set(portList[0])

    def connectPort(self):
        if self.portStatus == 'disconnected':
            self.selPort = self.combo.get()
            # if disconnected, then connect to selected port
            self.comm.connect(self.selPort)  # TODO check if need assignment
            # change button label
            # two ways of doing it: config(text=) and dict['text']
            self.btn2.config(text='Disconnect')
            # self.btn2['text'] = 'Disconnect'
            # update connection status
            self.portStatus = 'connected'
        elif self.portStatus == 'connected':
            # if connected, then disconnect from the port connected to
            self.disconnectPort(self.selPort)
            # change button label
            self.btn2['text'] = 'Connect'
            # update connection status
            self.portStatus = 'disconnected'
        else:
            print('No such port. Try again!!!')

    def disconnectPort(self, selPort):
        self.comm.disconnect(selPort)
        print("Port: %s disconnected" % selPort)

    def testing(self):
        self.test_lbl.config(text=self.chk_var.get())
        # print(self.comm)
        # print(self.portStatus)
        # print(self.selPort)

    def saveConfig(self):
        chk_value = self.chk_var.get()
        D = {'autoConnect': chk_value, 'comPort': 'COM5', 'selPort': 1}
        print(D)
        f = open('dubrovnik.pkl', 'wb')
        pickle.dump(D, f)
        f.close()


if __name__ == '__main__':

    from dubLibs import boardcom

    # serCom = SerComInterface()
    serCom = SerComInterface(DEBUG=True)
    comm = boardcom.BoardComm()  # create an instance of class Comm
    portList = comm.findPorts()
    serCom.combo.set(portList[0])
    serCom.comm = comm
    if serCom.autoConnect:
        serCom.connectPort()

    mainloop()

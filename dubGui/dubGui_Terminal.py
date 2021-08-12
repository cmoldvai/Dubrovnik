import sys
import pickle
from tkinter import *
from tkinter import ttk


class SerCom(Frame):

    def __init__(self, parent=None, DEBUG=False):
        LabelFrame.__init__(
            self, parent, text='Serial Connection', padx=10, pady=10)
        self.pack(side=TOP, anchor=NW, padx=10, pady=10)
        self.DEBUG = DEBUG
        self.comm = None                      # object created by boardcom
        self.portStatus = 'disconnected'
        self.selPort = ''  # ! keeps track of selected port, between calls
        self.portList = []
        self.portHandle = None
        self.chk_var = IntVar()
        self.autoConnect = 0
        self.chk_var.get()
        self.buildFrame()

    def buildFrame(self):
        '''Makes a reusable frame for a connecting to Dubrovnik board'''
        chk = Checkbutton(self, text='Auto connect', variable=self.chk_var)
        chk.grid(row=0, column=0)
        self.chk_var.set(self.autoConnect)

        self.combo = ttk.Combobox(
            self, width=10, values=self.portList, postcommand=self.updtPortList)
        self.combo.grid(row=0, column=1, padx=10)

        self.btn2 = Button(self, text='Connect', width=10,
                           command=self.connectPort)
        self.btn2.grid(row=0, column=2, padx=10)

        if self.DEBUG:
            self.test_btn = Button(self, text='Testing', width=10, command=self.testing)
            self.test_btn.grid(row=1, column=0, padx=5, pady=10, columnspan=1)
            self.test_lbl = Label(
                self, text="Debug message:", anchor=W, justify='left')
            self.test_lbl.grid(row=1, column=1, padx=5,
                               pady=10, sticky=EW, columnspan=3)

    def updtPortList(self):
        self.portList = self.comm.findPorts()
        self.combo['values'] = self.portList
        self.combo.set(portList[0])

    def connectPort(self):
        if self.portStatus == 'disconnected':
            self.selPort = self.combo.get()
            # if disconnected, then connect to selected port
            self.portHandle = self.comm.connect(
                self.selPort)  # TODO check if need assignment
            self.setSerialParams()
            self.btn2.config(text='Disconnect')
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
        serParams = '%s, baud=%d, bytes=%1d,\nparity=%s, stop=%1d, protocol=%s' \
            % (self.comPort, self.comBaudrate, self.comBytesize, self.comParity, self.comStopbits, self.comXonXoff)
        self.test_lbl.config(text=serParams)

    def setSerialParams(self):
        """
        docstring
        """
        self.comPort = self.portHandle.port
        self.comBaudrate = self.portHandle.baudrate
        self.comBytesize = self.portHandle.bytesize
        self.comParity = self.portHandle.parity
        self.comStopbits = self.portHandle.stopbits
        self.comXonXoff = self.portHandle.xonxoff


if __name__ == '__main__':

    from dubLibs import boardcom

    # serCom = SerComInterface()
    serCom = SerCom(DEBUG=True)
    comm = boardcom.BoardComm()  # create an instance of class Comm
    portList = comm.findPorts()
    serCom.combo.set(portList[0])
    serCom.comm = comm
    if serCom.autoConnect:
        serCom.connectPort()

    mainloop()

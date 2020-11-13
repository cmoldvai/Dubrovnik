import sys
from tkinter import *
from dubLibs import boardcom
from dubLibs import dubrovnik as du
from tkinter import ttk


class ConnectPort(Frame):

    def __init__(self, parent=None):
        LabelFrame.__init__(self, parent,text='Connection',padx=5,pady=5)  # do a superclass init
        self.pack(padx=10,pady=10)
        self.comm = 0
        self.comPort = 0 
        self.portStatus = 0
        self.selPort = ''
        self.portList = boardcom.find_ports()
        self.makeConnectFrame()
        self.cbox.current(0)

    def updtPortList(self):
        self.portList = boardcom.find_ports()
        self.cbox['values'] = self.portList
        self.comPort = self.cbox.get()

    def connectPort(self):
        if self.portStatus == 0:
            self.selPort = self.cbox.get()  
            self.comm = boardcom.connect2port(self.selPort)
            self.btn2['text'] = 'Disconnect'
            self.portStatus = 1
        elif self.portStatus == 1:
            self.disconnectPort(self.selPort)
            self.btn2['text'] = 'Connect'
            self.portStatus = 0
        else: 
            print('No such port. Try again!!!')

    def disconnectPort(self,selPort):
        del(self.comm)
        print("Port: %s disconnected" % selPort)

    def findPorts(self):
        self.portList = boardcom.find_ports()

    def makeConnectFrame(self):
        '''Makes a reusable frame for a connecting to Dubrovnik board'''
        self.cbox = ttk.Combobox(self, width=10, values=self.portList, postcommand=self.updtPortList)
        self.cbox.grid(row=1, column=0, padx=10)
        # cbox.current(0)

        self.btn2 = Button(self, width=12, text='Connect', command=self.connectPort)
        self.btn2.grid(row=1, column=1, padx=10)

        # var = IntVar()
        # chk = Checkbutton(self,text='Auto connect', variable=var)
        # chk.grid(row=1,column=4)
        # if var.get() == 1:
        #     partList = findPorts()
        #     port = partList[0]
        #     connectPort(port)


if __name__ == '__main__':

    root = Tk()
    root.geometry('300x150')
    frm = LabelFrame(root,text='Connect').pack(side=TOP)
    
    ConnectPort().mainloop()

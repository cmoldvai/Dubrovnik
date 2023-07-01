import sys
from tkinter import *
from tkinter import ttk


class YouTubeFrame(Frame):

    def __init__(self, parent=None, DEBUG=False):
        LabelFrame.__init__(
            self, parent, text='YouTube Downloader', padx=10, pady=10)
        self.pack(side=TOP, anchor=NW, padx=10, pady=10)

        self.itemList = ['abc', 'def', 'ghi']
        self.var1 = 0
        self.chk_var = IntVar()
        self.chk_var.get()
        self.buildFrame()

    def buildFrame(self):
        '''Makes a reusable frame'''
        chk = Checkbutton(self, text='URL:', variable=self.chk_var)
        chk.grid(row=0, column=0)
        self.chk_var.set(self.var1)

        self.combo = ttk.Combobox(
            self, width=10, values=self.itemList, postcommand=self.testFunc)
        self.combo.grid(row=0, column=1, padx=10)

        self.btn2 = Button(self, text='Connect', width=10,
                           command=self.testFunc)
        self.btn2.grid(row=0, column=2, padx=10)

        self.btn3 = Button(self, text='Save Config', width=10,
                           command=self.testFunc)
        self.btn3.grid(row=0, column=3, padx=10, sticky=E)

    def testFunc(self):
        print('testFunc')

    def updtPortList(self):
        self.itemList = self.testFunc()
        self.combo['values'] = self.itemList
        self.combo.set(self.itemList[0])

    # def saveConfig(self):
    #     chk_value = self.chk_var.get()
    #     D = {'autoConnect': chk_value, 'comPort': 'COM5', 'selPort': 1}
    #     print(D)
    #     # f = open('dubrovnik.pkl', 'wb')
    #     # pickle.dump(D, f)
    #     # f.close()


if __name__ == '__main__':

    ytF = YouTubeFrame(DEBUG=True)
    # comm = boardcom.BoardComm()  # create an instance of class Comm
    # portList = comm.findPorts()
    # serCom.combo.set(portList[0])
    # serCom.comm = comm
    # if serCom.autoConnect:
    #     serCom.connectPort()

    mainloop()

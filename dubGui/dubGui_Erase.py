import sys
from tkinter import *
from dubLibs import dubrovnik as du

class Erase(Frame):

    def __init__(self, parent=None, DEBUG=False):
        LabelFrame.__init__(self, parent, text='Erase', padx=5, pady=5)
        self.pack(side=TOP, anchor=NW, padx=10, pady=10)
        self.DEBUG = DEBUG
        self.comm = None
        self.pageSize = 0x100
        self.blockSize = StringVar()
        self.startAddr = StringVar()
        self.numBlocks = StringVar()
        self.blockSizes = ['4', '32', '64', 'Chip']
        self.buildFrame()
        self.blockSize.set(self.blockSizes[0])

    def buildFrame(self):
        '''Makes a reusable frame for a flash erase operation'''
        rb1 = Radiobutton(self, text='4kB', variable=self.blockSize,
                          value=self.blockSizes[0]).grid(row=1, column=0, padx=20, pady=5)
        rb2 = Radiobutton(self, text='32kB', variable=self.blockSize,
                          value=self.blockSizes[1]).grid(row=1, column=1, padx=20, pady=5)
        rb3 = Radiobutton(self, text='64kB', variable=self.blockSize,
                          value=self.blockSizes[2]).grid(row=1, column=2, padx=20, pady=5)
        rb4 = Radiobutton(self, text='Chip', variable=self.blockSize,
                          value=self.blockSizes[3]).grid(row=1, column=3, padx=20, pady=5)

        lbl = Label(self, text='Start Address:  0x').grid(
            row=2, column=0, padx=0, pady=2, sticky=E)
        ent1 = Entry(self, textvariable=self.startAddr).grid(
            row=2, column=1, sticky=W)
        self.startAddr.set('0')

        lbl2 = Label(self, text='Number of Blocks:  0x').grid(
            row=3, column=0, padx=0, pady=2, sticky=E)
        ent2 = Entry(self, textvariable=self.numBlocks).grid(
            row=3, column=1, sticky=W)
        self.numBlocks.set('3')

        lbl3 = Label(self, text='Length:  0x').grid(
            row=4, column=0, padx=0, pady=2, sticky=E)
        lbl4 = Label(self, text='Result here').grid(row=4, column=1, sticky=W)

        btn2 = Button(self, text='Erase',
                      command=self.blockErase).grid(row=5, column=0, padx=10, pady=10)

        if self.DEBUG:                      
            quit_btn = Button(self, text='Quit', command=sys.exit)
            quit_btn.grid(row=5, column=3, padx=10, pady=10)

    def blockErase(self):
        blkSzStr = self.blockSize.get()

        if blkSzStr == 'Chip':
            print('Erasing entire chip')
            self.comm.send('6; 60; wait 0')
            print(self.comm.response())
            print('Chip erase done.')
        else:
            # must be in else, otherwise it fails for 'Chip'
            block_size = int(blkSzStr)
            start_addr = int(self.startAddr.get(), 16)
            # # Calculating the actual start addresses:
            # mask = ~((block_size * 1024) - 1)  # pay attention: tricky
            # actStartAddr = start_addr & mask
            print(f'Start address = {start_addr:x}')
            # print(f'Actual start address = {actStartAddr:x}')
            numm_blocks = int(self.numBlocks.get())
            print(f'Erasing {numm_blocks} {block_size}kB block(s)')
            du.block_erase(self.comm, block_size=block_size,
                           start_addr=start_addr, num_blocks=numm_blocks)
            print('Block erase done.')

        print('Elapsed time: {}ms')

    def message(self):
        self.data += 1
        print('Hello from world %s!' % self.data)


if __name__ == "__main__":

    from dubLibs import boardcom
    
    comm = boardcom.BoardComm()
    portList = comm.findPorts()
    port = portList[0]
    connectedPort = comm.connect(port)
    Erase().comm = comm 
    # Erase(DEBUG=True).comm = comm
    
    mainloop()

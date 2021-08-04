# import pandas as pd
# import numpy as np
import matplotlib.pyplot as plt
import debugging as dbg
from dubLibs import boardcom
from dubLibs import dubrovnik as du


def plot_vt(x, y, i, delay):
    fig1, axes1 = plt.subplots(figsize=(8,6))
    # plt.tight_layout()
    axes1.set_title(f'$V_T$ Distribution (delay={delay}ms)')
    axes1.set_xlabel('$V_T$ [V]')
    axes1.set_ylabel('Number of cells')
    axes1.semilogy(x, y, color='#0070C0')
    axes1.set_xlim([1,11])
    axes1.set_ylim([.6, 1.5*max(y)])
    axes1.tick_params(axis='both', labelsize=8)
    axes1.grid(True, color='.6', dashes=(5,2,1,2))
    axes1.set_facecolor('#F8F8F8')
    # plt.show()

    filename = f'./dubScripts/plots/{i:02d}_vt_curve_dly_{delay}ms.png'
    fig1.savefig(filename, dpi=200)


# import os
# print(os.getcwd())
# os.chdir('./dubScripts/plots')
# print(os.getcwd())

comm = boardcom.BoardComm()   # create an instance of class BoardComm
portList = comm.findPorts()
print(portList)
connectedPort = portList[0]
comm.connect(connectedPort)
print('Connection established...')

start_addr = 0x0
end_addr = start_addr + 0x1000
numbytes = end_addr - start_addr

num_erase = 10   # number of times a block of memory is erased
block_size = 4  # must be 4, 32 or 64

for i in range(num_erase):
    du.block_erase(comm, block_size=block_size, start_addr=start_addr, num_blocks=1, trig=False, echo=0)

print(f'{block_size}kB memory block erased {num_erase} times')
print(f'getting vt curves after {num_erase} Erase cycles')
dbg.runfdma(comm=comm, addr=start_addr, numbytes=numbytes, prefix="", fast=True, nocpsum=False,
            minvdac=0, maxvdac=63, with_nbias=True, plot=True)
print('painting memory 8 times with a pattern')

for i in range(2):
    du.pattern_program(comm, start_addr=start_addr, end_addr=end_addr, pattern='55aa55aa', increment=0, echo=0)

print('getting vt curves after painting memory')
dbg.runfdma(comm=comm, addr=start_addr, numbytes=numbytes, prefix="", fast=True, nocpsum=False,
            minvdac=0, maxvdac=63, with_nbias=True, plot=True)

delay = 0      # initial delay
dly_step = 2   # [ms]
print("\n*****************\nSuspend Erase:")

if block_size == 4:
    cmdstr = f'06; 20 {start_addr}; delay {delay*1000}; b0; wait 0'
elif block_size == 32:
    cmdstr = f'06; 53 {start_addr}; delay {delay*1000}; b0; wait 0'
elif block_size == 64:
    cmdstr = f'06; d8 {start_addr}; delay {delay*1000}; b0; wait 0'
else:
    print('Block size incorrect!!!')
    cmdstr = f'06; d8 {start_addr}; delay {delay*1000}; b0; wait 0'
print(cmdstr)
comm.send(cmdstr)

max_erase_time = 60   # in [ms]
N = int(max_erase_time // dly_step)

for i in range(N):
    print(f'getting vt curves after Erase -> {delay}ms delay -> EraseSuspend')
    df = dbg.runfdma(comm=comm, addr=start_addr, numbytes=numbytes, prefix="", fast=True, nocpsum=False,
                     minvdac=0, maxvdac=63, with_nbias=True, plot=False)
    print('process DataFrame')
    plot_vt(df.vt, df.psum, i, delay)

    delay += dly_step

    # Resume Erase; Wait specified delay time; Suspend Erase again
    cmdstr = f'd0; delay {delay*1000}; b0; wait 0'
    print(cmdstr)
    comm.send(cmdstr)
    print(f'Resume Erase -> delay {delay}ms -> Suspend Erase')

cmdstr = 'd0; wait 0'
print(cmdstr)
comm.send(cmdstr)
print("Resume Erase. Let it finish!!!")

dbg.runfdma(comm=comm, addr=start_addr, numbytes=numbytes, prefix="", fast=True, nocpsum=False,
            minvdac=0, maxvdac=63, with_nbias=True, plot=True)

# ***********************************
# ***** Disconnect, Delete Port *****
# ***********************************
comm.disconnect(connectedPort)
del comm
print('\nDisconnected...')
print("COM port deleted\n")

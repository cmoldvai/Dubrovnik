import matplotlib.pyplot as plt
from dubLibs import boardcom
from dubLibs import dubrovnik as du
from dubLibs import debugging as dbg


def plot_vt(x, y, i, delay):
    fig1, axes1 = plt.subplots(figsize=(8, 6))
    # plt.tight_layout()
    axes1.set_title(f'$V_T$ Distribution (delay={delay}ms)')
    axes1.set_xlabel('$V_T$ [V]')
    axes1.set_ylabel('Number of cells')
    axes1.semilogy(x, y, color='#0070C0')
    axes1.set_xlim([1, 11])
    axes1.set_ylim([.6, 1.5*max(y)])
    axes1.tick_params(axis='both', labelsize=9)
    axes1.grid(True, color='.6', dashes=(5, 2, 1, 2))
    axes1.set_facecolor('#F8F8F8')
    # plt.show()

    filename = f'./dubScripts/plots/{i:02d}_vt_curve_dly_{delay}ms.png'
    fig1.savefig(filename, dpi=200)


def block_erase_str(start_addr, block_size):
    if block_size == 4:
        erase_str = f"06; 20 {start_addr:x};"
    elif block_size == 32:
        erase_str = f"06; 52 {start_addr:x};"
    elif block_size == 64:
        erase_str = f"06; d8 {start_addr:x};"
    else:
        comm.disconnect(connectedPort)
        raise ValueError("Incorrect block size")
    return erase_str


# *********************
# *****  Connect  *****
# *********************
comm = boardcom.BoardComm()   # create an instance of class BoardComm
connectedPort = comm.find_and_connect(echo=1)

start_addr = 0x8000
length = 0x400
end_addr = start_addr + length
numbytes = end_addr - start_addr
num_erase = 4           # number of times a block of memory is erased
block_size = 4         # must be 4, 32 or 64
delay = 0               # initial delay
dly_step = 10            # [ms]
max_delay = 60          # in [ms]

# don't let it continue if a wrong Erase block size was entered
if block_size != 4 and block_size != 32 and block_size != 64:
    comm.disconnect(connectedPort)
    raise ValueError("Incorrect block size")

for j in range(num_erase):
    du.block_erase(comm, block_size=block_size, start_addr=start_addr,
                   num_blocks=1, trig=False, echo=0)

print(f'Get Vt after {block_size}kB memory block erased {num_erase} times')
df = dbg.get_vt_curves(comm=comm, addr=start_addr, numbytes=numbytes, prefix="", fast=True, nocpsum=False,
                       minvdac=0, maxvdac=63, with_nbias=True, plot=True)

# Paint memory with a pattern
for j in range(2):
    du.pattern_program(comm, start_addr=start_addr,
                       end_addr=end_addr, pattern='55aa55aa', increment=0, echo=0)

print(f'Get Vt after memory painted with a pattern')
df = dbg.get_vt_curves(comm=comm, addr=start_addr, numbytes=numbytes, prefix="", fast=True, nocpsum=False,
                       minvdac=0, maxvdac=63, with_nbias=True, plot=True)
plot_vt(df.vt, df.psum, i=0, delay="_")

# Loop for: Erase, Suspend, Variable Delay, Resume
i = 1
while delay <= max_delay:
    print(f"\n***** Cycle: {i} *****")

    # Erase the memory block in use num_erase times, to establish baseline distrubution
    for j in range(num_erase):
        du.block_erase(comm, block_size=block_size, start_addr=start_addr,
                       num_blocks=1, trig=False, echo=0)

    # Paint memory with a pattern
    for j in range(2):
        du.pattern_program(comm, start_addr=start_addr,
                           end_addr=end_addr, pattern='55aa55aa', increment=0, echo=0)

    # Start an Erase operation, delay and suspend
    cmdstr = block_erase_str(start_addr, block_size) + \
        f" delay {delay*1000}; b0"
    print(cmdstr)
    comm.send(cmdstr)

    # print(f'getting vt curves after Erase -> {delay}ms delay -> EraseSuspend')
    df = dbg.get_vt_curves(comm=comm, addr=start_addr, numbytes=numbytes, prefix="", fast=True, nocpsum=False,
                           minvdac=0, maxvdac=63, with_nbias=True, plot=False)

    plot_vt(df.vt, df.psum, i, delay)

    delay += dly_step
    i += 1

    cmdstr = f"d0; wait 0"  # Resume Erase. Let it finish!
    print(cmdstr)
    comm.send(cmdstr)

# ************************
# *****  Disconnect  *****
# ************************
comm.disconnect(connectedPort, echo=1)

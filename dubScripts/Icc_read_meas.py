import os
import time

from dubLibs import boardcom, dubrovnik


def paint_memory(mem_params):
    '''Erase specific number of memory blocks with specified pattern'''

    # before programming, erase the memory
    print('\nErasing memory blocks...')
    for i, item in enumerate(mem_params):
        du.block_erase(
            comm, start_addr=item[0], block_size=4, num_blocks=4, echo=1)

    print('Wait!!! Painting memory...')
    prog_time = du.paint_flash_with_pattern(comm, mem_params)
    prog_time = du.time_conv_from_usec(prog_time)
    print(f'Programming time: {prog_time}')


os.system('cls')  # clear terminal screen
# print(sys.path)

# *********************************
# *****        M A I N        *****
# *********************************

# *********************
# *****  Connect  *****
# *********************
comm = boardcom.BoardComm()   # create an instance of the class
du = dubrovnik.Dubrovnik()  # create an instance of the class
connectedPort = comm.find_and_connect(echo=1)

# ENTER System Parameters Here
deviceNum = '01'
temperature = '25C'
pmon_id = '5'
PAINT_MEMORY = True  # True/False

du.set_dispmode(comm, 'w')
config = du.get_config(comm)
partNumber = config['Part#']
voltage = config['Voltage']
freq = config['Frequency']

print(f"Device Number : {deviceNum}")
print(f"Part Number   : {partNumber}")
print(f"Voltage       : {voltage}V")
print(f"Frequency     : {freq}MHz")

print('Status Registers:')
du.read_id(comm, narg=2)

page_size = 0x100

# PAINT MEMORY BIT PATTERN
# ******************************
# 0x0000-0x3fff   : "aaaaaaaa"
# 0x4000-0x7fff   : "00000000"
# 0x8000-0xbfff   : "ffffffff"
# 0xc000-0xffff   : "f0f0f0f0"
# 0x10000-0x13fff : "ff00ff00"
# ******************************

paint_flash_params = [[0x0000, 0x4000, 'aaaaaaaa'],
                      [0x4000, 0x4000, '00000000'],
                      [0x8000, 0x4000, 'ffffffff'],
                      [0xc000, 0x4000, 'f0f0f0f0'],
                      [0x10000, 0x4000, 'ff00ff00']]

if PAINT_MEMORY is True:
    paint_memory(paint_flash_params)

for param in paint_flash_params:
    du.read(comm, param[0], 0x20, echo=1)

# '''
# *************************************************
# *****     READ DEVICE - MEASURE CURRENT     *****
# *************************************************

print('Read device')

fname = f'{partNumber} UNIT {deviceNum} {temperature}.txt'
file = open(fname, 'w')
file.write(f'Part Number: {partNumber}\n')
file.write(f'Temperature: {temperature}\n')
file.write(f'Unit: {deviceNum}\n')
file.write(
    ' Mode  Vcc[V] freq[MHz] Icc1[mA] t_elapsed[us] num_errors start_address\n')
file.write(
    ' ----------------------------------------------------------------------\n')

# spi_mode = ['spi', 'q114', 'q144', 'q044']
# set_voltage = [3, 3.3, 3.6]
# set_freq = [10, 20, 40, 60, 80]
spi_mode = ['spi', 'q144']
set_voltage = [1.8]
set_freq = [64]

# To make sure device is not damaged during test
# verify if selected voltages are withing device limits
for v in set_voltage:
    v_max = float(voltage) + 0.3
    # If voltage is larger than abs max disconnect and quit
    if v > v_max:
        print('\nCAUTION!!!\n')
        print(
            f'Specified voltage: {v:.3f}V exceeds device Abs Max Limits: {v_max:.3f}V\n')
        comm.disconnect(connectedPort, echo=1)
        quit()

icc_results = []
tot_error_cnt = 0
err_cnt = 0

for mode in spi_mode:
    # ATTENTION: IMPORTANT!!!
    # Set QE mode to 1. This command may be different for different devices
    if mode[0].lower() == 'q':
        comm.send('6; 31 2')
        comm.send('35')
        start_addr = paint_flash_params[3][0]
        wr_buff = paint_flash_params[3][2]
    else:
        comm.send('6; 31 0')
        comm.send('35')
        start_addr = paint_flash_params[0][0]
        wr_buff = paint_flash_params[0][2]

    print(f'Start Address: 0x{start_addr:x}\n')
    addr = start_addr

    print('Read Status Registers - checking QE bit:')
    comm.send('05; 35')
    comm.response()

    # start_addr = du.wr_buffer(comm, mode)
    read_opcode = du.set_spi_mode(mode)
    print(f'MODE: {mode}')

    for v in set_voltage:
        comm.send(f'psset 0 {v}')       # set voltage

        for f in set_freq:
            comm.send(f'freq {f}')   # set frequency
            read_str = ''
            addon = ''

            N = 16
            read_block_size = 0x4000
            block = f'{read_block_size:x}'

            for i in range(0, N):
                if mode == 'q144':
                    addon = f'{read_opcode} {addr:x} 00 {block};'
                elif mode == 'q044':
                    if i == 0:
                        addon = f'eb {addr:x} a0 {block};'
                    elif i == N-1:
                        addon = f'ebc {addr:x} 00 {block};'
                    else:
                        addon = f'ebc {addr:x} a0 {block};'
                else:
                    addon = f'{read_opcode} {addr:x} {block};'
                read_str += addon
                # print(f'addon: {addon}')

            # All power monitoring commands are inline with page programming
            # to exclude delays introduced by Python interpreter
            read_str = f'pmon {pmon_id} start;timer start;{read_str} timer stop; pmon {pmon_id} stop'
            print(read_str)

            comm.send('echo off')
            start_time = time.time()
            comm.send(read_str)
            # print(comm.response())
            end_time = time.time()
            comm.send('echo on')
            comm.send('dvar elapsed_time')
            e_time = comm.response().split('\n')
            print(e_time[1])
            comm.send(f'pmon {pmon_id} calc')
            pmon1 = comm.response()
            print(pmon1)

            elapsed_time = str(round(end_time - start_time, 3))
            print(f'Total elapsed time: {elapsed_time}\n')

            # ********************************
            # *****     SAVE RESULTS     *****
            # ********************************
            ch1 = pmon1.index('=')      # find index for '='
            ch2 = pmon1.index('mA')     # find index for \n>>>
            # between these is the current read and remove the 'mA' from the string
            icc1 = pmon1[ch1 + 1: ch2 - 1]

            # Verifying if the read memory matches the write buffer
            # load write buffer with reference values
            comm.send(f'pattern {wr_buff} 0')
            # compare content of read and write buffers
            comm.send(f'cmp 0 {read_block_size:x}')
            comp_result_msg = comm.response()

            SAVE_ERR_MSG = 0  # 0 or 1
            # if response does not contatin the word 'equal', the 'read' and 'write' buffers are different
            if not('equal' in comp_result_msg.lower()):
                # print(comp_result_msg)
                if SAVE_ERR_MSG == 1:
                    file.write(f'{comp_result_msg}\n')
                err_msg = comp_result_msg.split('\n')[-1]
                print(err_msg)
                try:
                    err_cnt = int(err_msg.split()[-2])
                except:
                    print(
                        'Buffer overload!!! Printout of differences not available.\n\
                            Use cmp TestBench command from terminal to further explore')
                    err_cnt = -1
                tot_error_cnt += 1

            file.write(
                f'{mode:>5s} {v:>6.2f}     {f:>5.2f}  {icc1:>7s}   {e_time[1][:-2]:>12s}     {err_cnt:>6d}    {start_addr:>10x}\n')
            err_cnt = 0

file.write(f'\nNumber of failed cases {tot_error_cnt}\n')

file.close()
# '''

# ************************
# *****  Disconnect  *****
# ************************
comm.disconnect(connectedPort, echo=1)

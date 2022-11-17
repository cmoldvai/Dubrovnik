import os
# import sys
import time

from dubLibs import boardcom, dubrovnik


def paint_memory():
    # ****** Erase specific number of memory blocks *******
    du.block_erase(comm, num_blocks=20, block_size=4, echo=0)

    # ****** Paint the memory with specific data pattern *******
    prog_time = du.paint_flash_with_pattern(comm, paint_flash_params)
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
PAINT_MEMORY = False  # True/False

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


# ******************************
#   Program Flash with Pattern
# ******************************
# 0x0000-0x3fff   : "aaaaaaaa"
# 0x4000-0x7fff   : "00000000"
# 0x8000-0xbfff   : "ffffffff"
# 0xc000-0xffff   : "f0f0f0f0"
# 0x10000-0x13fff : "ff00ff00"

page_size = 0x100
paint_flash_params = [[0x0000, 0x4000, 'aaaaaaaa'],
                      [0x4000, 0x4000, '00000000'],
                      [0x8000, 0x4000, 'ffffffff'],
                      [0xc000, 0x4000, 'f0f0f0f0'],
                      [0x10000, 0x4000, 'ff00ff00']]

if PAINT_MEMORY == True:
    print('\nWait!!! Painting memory with specified bit pattern...\n')
    paint_memory()

for param in paint_flash_params:
    du.read(comm, param[0], 0x40, echo=1)

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

spi_mode = ['spi', 'q114', 'q144', 'q044']
# spi_mode = ['spi', 'q114', 'q144', 'q044']
set_voltage = [1.8]
# set_voltage = [3, 3.3, 3.6]
set_freq = [32]
# set_freq = [10, 20, 40, 60, 80]

for v in set_voltage:
    v_max = float(voltage) + 0.3
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
    else:
        comm.send('6; 31 0')
        comm.send('35')
        start_addr = paint_flash_params[0][0]

    print(f'Start Address: 0x{start_addr:x}\n')
    addr = start_addr

    print('Read Status Registers - checking QE bit:')
    comm.send('05; 35')
    comm.response()

    # start_addr = du.wr_buffer(comm, mode)
    read_opcode = du.set_spi_mode(mode)
    print(f'MODE: {mode}')

    for v in set_voltage:
        comm.send(f'volt {v}')       # set voltage
        for f in set_freq:
            comm.send(f'freq {f}')   # set frequency
            read_str = ''
            addon = ''

            N = 16
            read_block_size = 0x4000
            block = f'{read_block_size:x}'

            for i in range(0, N):

                if i == 0:           # in the first loop generate FRAMING pulses with GPIOs for scope triggering
                    # if SPI MODE is '144' or '044' then we need to add MODE BITS (a0h or 00h) to the command line
                    if mode == 'q144':
                        addon = f'gpiowr 7 1;{read_opcode} {addr:x} 00 {block};gpiowr 7 0;'
                    elif mode == 'q044':
                        addon = f'gpiowr 7 1;eb {addr:x} a0 {block};gpiowr 7 0;'
                    else:
                        addon = f'gpiowr 7 1;{read_opcode} {addr:x} {block};gpiowr 7 0;'
                elif i == N - 1:
                    if mode == 'q044':
                        addon = f'{read_opcode} {addr:x} 00 {block};'
                    else:
                        pass
                else:               # in the rest of the loop don't generate FRAMING pulses
                    # if SPI MODE = '1-4-4' then we need to add the MODE BITS ('0') to the string
                    if mode == 'q144':
                        addon = f'{read_opcode} {addr:x} 00 {block};'
                    elif mode == 'q044':
                        addon = f'{read_opcode} {addr:x} a0 {block};'
                    else:
                        addon = f'{read_opcode} {addr:x} {block};'
                read_str += addon
                print(f'addon: {addon}')

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
            ch1 = pmon1.index('=')         # find index for '='
            ch2 = pmon1.index('mA')     # find index for \n>>>
            # between these is the current read and remove the 'mA' from the string
            icc1 = pmon1[ch1 + 1: ch2 - 1]

            # verifying if the read memory matches the write buffer
            comm.send('cmp 0 {read_block_size:x}')
            comp_result_msg = comm.response()
            print(comp_result_msg)

            SAVE_ERR_MSG = 0
            if not('equal' in comp_result_msg.lower()):
                print(comp_result_msg)
                if SAVE_ERR_MSG == 1:
                    file.write(f'{comp_result_msg}')
                err_msg = comp_result_msg.split('\n')[-2]
                err_cnt = int(err_msg.split(' ')[1])
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

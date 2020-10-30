import os
import sys
import time
from dubLibs import boardcom
from dubLibs import dubrovnik as du

os.system('cls')  # clear terminal screen
# print(sys.path)


##################################
#####        M A I N        ######
##################################

# Connecting to the board
defaultPort = 5
comm = boardcom.detect_ports(defaultPort)

# ENTER System Parameters Here
freq = 8          # chose 8 (8.25), 15 (14.67) or 30 (29.33)
deviceNum = '01'
temperature = '25C'
pmon_id = '5'

comm.send('freq ' + str(freq))
comm.send('dispmode w')

# Read board configuration and reset the chip
comm.send('config')
cfg = comm.responselines()
# print(cfg)

partNumber = cfg[0].split('=')[1].split(' ')[1].upper()
voltage = cfg[1].split('=')[1].split(' ')[1]
freq = cfg[2].split('=')[1].split(' ')[1]

print(f"Device Number : {deviceNum}")
print(f"Part Number   : {partNumber}")
print(f"Voltage       : {voltage}V")
print(f"Frequency     : {freq}MHz")

print('Status Registers:')
du.read_id(comm, narg=2)

# # ****** Erase specific number of memory blocks *******
du.erase_memory_block(comm, num_blocks=16, block_size=4)

# # ****** Program memory blocks with variety of patterns for current measurement
du.flash_program(comm)

# '''
#################################################
#####     READ DEVICE - MEASURE CURRENT     #####
#################################################

print('Read device')

fname = partNumber + ' UNIT ' + \
    deviceNum + ' ' + temperature + '.txt'
file = open(fname, 'w')
file.write('Part Number: %s \n' % partNumber)
file.write('Temperature: %s\n' % temperature)
file.write('Unit: %s \n' % deviceNum)
file.write(
    ' Mode  Vcc[V] freq[MHz] Icc1[mA] t_elapsed[us] num_errors start_address\n')
file.write(
    ' ----------------------------------------------------------------------\n')

#spi_mode = ['q144']
spi_mode = ['spi', 'q144']
#spi_mode = ['spi', 'q114', 'q144', 'q044']
#set_voltage = [3.3]
set_voltage = [3, 3.3, 3.6]
set_freq = [10, 20, 40]
#set_freq = [10, 20, 40, 60, 80]

icc_results = []
tot_error_cnt = 0
err_cnt = 0
# error_msg = 'pass'

for mode in spi_mode:
    # ATTENTION: IMPORTANT!!!
    # Set QE mode to 1
    # This command may be different for different devices
    if mode[0].lower() == 'q':
        du.cmd(comm, '6; 31 2', echo=1)
        du.cmd(comm, '35', echo=1)
    else:
        du.cmd(comm, '6; 31 0', echo=1)
        du.cmd(comm, '35', echo=1)

    print('Read Status Registers - checking QE bit:')
    du.cmd(comm, '05; 35', echo=1)

    start_addr = du.wr_buffer(comm, mode)
    read_opcode = du.set_mode(mode)
    print('MODE: %s\n' % mode)
    for v in set_voltage:
        du.cmd(comm, 'volt ' + str(v), echo=1)         # set voltage
        for f in set_freq:
            du.cmd(comm, 'freq ' + str(f), echo=1)     # set frequency
            read_str = ''
            addon = ''
            # read configuration to get current voltage and frequency
            comm.send('config')
            config = comm.response()
            voltage = config.split('\n')[2].split('=')[1].split(' ')[1]
            frequency = config.split('\n')[3].split('=')[1].split(' ')[1]
            # print(voltage)
            # print(frequency)

            N = 16
            read_block_size = 0x4000
            block = format(read_block_size, 'X')

            print('Start Address: 0x%X\n' % start_addr)
            for i in range(0, N):
                addr = start_addr    # read_block_size * i
                if i == 0:       # generate FRAMING pulses with GPIOs for scope triggering
                    # if SPI MODE = '1-4-4' then we need to add the MODE BITS ('0') to the string
                    if mode == 'q144':
                        #addon = read_opcode + ' 0 ' + format(addr, 'X') + ' ' + block + ';'
                        addon = 'gpiowr 7 1;' + read_opcode + ' ' +\
                            format(addr, 'X') + ' 00 ' + block + ';gpiowr 7 0;'
                    elif mode == 'q044':
                        addon = 'gpiowr 7 1;' + 'eb' + ' ' + \
                            format(addr, 'X') + ' a0 ' + block + ';gpiowr 7 0;'
                    else:
                        #addon = read_opcode + ' ' + format(addr, 'X') + ' ' + block + ';'
                        addon = 'gpiowr 7 1;' + read_opcode + ' ' + \
                            format(addr, 'X') + ' ' + block + ';gpiowr 7 0;'
                elif i == N-1:
                    if mode == 'q044':
                        addon = read_opcode + ' ' + \
                            format(addr, 'X') + ' 00 ' + block + ';'
                    else:
                        pass
                else:               # don't generate FRAMING pulses
                    # if SPI MODE = '1-4-4' then we need to add the MODE BITS ('0') to the string
                    if mode == 'q144':
                        addon = read_opcode + ' ' + \
                            format(addr, 'X') + ' 00 ' + block + ';'
                    elif mode == 'q044':
                        addon = read_opcode + ' ' + \
                            format(addr, 'X') + ' a0 ' + block + ';'
                    else:
                        addon = read_opcode + ' ' + \
                            format(addr, 'X') + ' ' + block + ';'
                read_str += addon
                print('addon: ' + addon)

            # All power monitoring commands are inline with page programming
            # to exclude delays introduced by Python interpreter

            read_str = 'pmon ' + pmon_id + ' start;timer start;' + \
                read_str + 'timer stop; pmon ' + pmon_id + ' stop'
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
            du.cmd(comm, 'pmon ' + pmon_id + ' calc', echo=0)
            pmon1 = comm.response()
            print(pmon1)

            elapsed_time = str(round(end_time - start_time, 3))
            print('Elapsed READ time: ' + elapsed_time + '\n')

            # Format results and store it for saving into a file

            ################################
            #####     SAVE RESULTS     #####
            ################################

            ch1 = pmon1.index('=')         # find index for '='
            ch2 = pmon1.index('\n>>>')     # find index for \n>>>
            # between these is the current read and remove the 'mA' from the string
            icc1 = pmon1[ch1+1: ch2-3]

            # verifying if the read memory matches the write buffer
            comm.send('cmp ' + ' 0 ' + format(read_block_size, 'X'))
            comp_result_msg = comm.response()

            if not('equal' in comp_result_msg):
                # print(comp_result_msg)
                err_cnt = int(comp_result_msg.split(' ')[-3])
                # error_msg = 'fail'
                tot_error_cnt += 1

            file.write('%5s %6s  %7s  %7s  %14s     %6d        %5X \n' %
                       (mode, voltage[:-1], frequency[:-1], icc1, e_time[1][:-2], err_cnt, start_addr))
            # error_msg = 'pass'
            err_cnt = 0

file.write('\nNumber of failed cases %d\n' % tot_error_cnt)

file.close()
# '''


############################
#####     CLEAN-UP     #####
############################
# This should be at the end of the script
del comm
print('\n***** CLEAN UP *****')
print("COM port deleted\n")

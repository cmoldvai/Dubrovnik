# import time
# from time import sleep
from dubLibs import boardcom
# from dubLibs import dubrovnik as du

print('*********************************')
print('***** DataFlash Read Script *****')
print('*********************************\n')

# os.system('cls')  # clear terminal screen
# print(sys.path)

# *********************
# *****  Connect  *****
# *********************
comm = boardcom.BoardComm()   # create an instance of class BoardComm
connectedPort = comm.find_and_connect(echo=1)


# #################################
# ####        M A I N        ######
# #################################

# ENTER System Parameters Here
freq = 20   # select between 8 to 60

cmd = 'freq ' + str(freq)
comm.send(cmd)

# Read SW version
comm.send('ver')
version = comm.response()
print(version)

# Read board configuration and reset the chip
comm.send('config')
cfg = comm.response()
print(cfg)
config = cfg.split('\n')
partNumber = config[1].split('=')[1].split(' ')[1].upper()
voltage = config[2].split('=')[1].split(' ')[1].lower()

dispmode = 'b'  # byte format
# dispmode = 'w'  # 32-bit word format

if dispmode == 'b':
    comm.send('dispmode b')
else:
    comm.send('dispmode w')

# **********************************
# ********* VER 1 ******************
# **********************************

# N = 4
# read_block_size = 0x400
# block = format(read_block_size, 'X')
# addr = 0

# f = open('memory_content.txt', 'w')
# for i in range(0, N):
#     addr = format(read_block_size * i, 'X')
#     str = '3 ' + addr + ' ' + block
#     comm.send(str)
#     resp = comm.response()
#     # print(resp)
#     f.write(resp)
# f.close()

# **********************************
# ********* VER 2 ******************
# **********************************

N = 2
read_block_size = 0x400
block = format(read_block_size, 'X')
addr = 0

f1 = open('memcontent.txt', 'w')
for i in range(0, N):
    addr = format(read_block_size * i, 'X')
    str = '3 ' + addr + ' ' + block
    comm.send(str)
    resp = comm.resp()
    # print(resp)

    for i in range(len(resp)):
        # print(resp[i])
        f1.write(resp[i])
        f1.write('\n')

f1.close()

# ###############################
# ####     CHIP PROGRAM     #####
# ###############################
# prog_pattern = 'caba0000'
# print('Starting programming chip page-by-page\n')
# pattern = prog_pattern + ' 0'
# comm.send('pattern ' + pattern)
# prog_str = ''
# start_time = time.time()
# start_addr = 8192 * stage
# end_addr   = start_addr + 8192
# #for i in range(0, 8192):    # 16MB(65536); 8MB(32768); 4MB(16384); 2MB(8192)
# for i in range(start_addr, end_addr): # 16MB(65536); 8MB(32768); 4MB(16384); 2MB(8192)
#     i_str = format(i, 'X')
#     n_str = format(256 * i, 'X')
#     if (i % 256) == 0:
#         print(i_str + ', ' + n_str)
#         prog_str = '06; gpiowr 7 1; 2 ' + n_str + ' 100; wait 0; gpiowr 7 0 '
#     else:
#         prog_str = '06; 2 ' + n_str + ' 100; wait 0; '
#     comm.send(prog_str)
# end_time = time.time()
# elapsed_time = str(round(end_time - start_time, 2))
# print('Program elapsed time: ' + elapsed_time + '\n')


# print('\n ********** Device Program/Erase/Read Test **********')
# if partNumber[0:2] == 'AT':          # device present
#     print('Device %s present' % partNumber)
#     print('VCC = %sV' % voltage)
#     print('Read Status Registers:')
#     comm.send('d7')           # status reg read
#     resp = comm.response().split('\n')
#     print('STSREG1: %s' % resp[1])
#     print('STSREG2: %s' % resp[2])

#     print('\n    Erasing block 0...')
#     comm.send('6;20 0; wait 0')      # erase block 0
#     print('    Reading...')
#     comm.send('b 0 20')              # read some data
#     resp = comm.response().split('\n')[1]
#     print('\t%s' % resp)

#     if 'ffffffff' in resp:
#         print('DEVICE ERASED')

#     # set up programming
#     print('\n    Programming...')
#     comm.send('pattern caba0000 1')
#     comm.send('06; 02 0 20; wait 0')
#     # read and compare 1st word
#     print('    Reading...')
#     comm.send('0b 0 20')
#     resp = comm.response().split('\n')[1]
#     print('\t%s' % resp)

#     if 'caba0000' in resp:
#         print('\nPROGRAM PASS')
#         print('\nREAD PASS')
#     else:
#         print('\nPROGRAM/READ FAIL')

#     print('\n    Erasing block 0...')
#     comm.send('6;20 0; wait 0')      # erase block 0
#     comm.send('0b 0 20')
#     resp = comm.response().split('\n')[1]
#     print('\t%s' % resp)

#     if 'ffffffff' in resp:
#         print('\nERASE PASS')
#     else:
#         print('\nERASE FAIL')


# ************************
# *****  Disconnect  *****
# ************************
comm.disconnect(connectedPort, echo=1)
print('*******************************')
print('******** TEST FINISHED ********')
print('*******************************\n')

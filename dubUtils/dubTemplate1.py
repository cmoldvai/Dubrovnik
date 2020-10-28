import os
import sys
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
freq = 8
pmon_id = '5'

du.board_cmd(comm, 'freq ' + str(freq))
du.board_cmd(comm, 'dispmode w')

# Read board configuration and reset the chip
comm.send('config')
cfg = comm.responselines()
# print(cfg)

partNumber = cfg[0].split('=')[1].split(' ')[1].upper()
voltage = cfg[1].split('=')[1].split(' ')[1]
freq = cfg[2].split('=')[1].split(' ')[1]

print(f"Part Number : {partNumber}")
print(f"Voltage     : {voltage}V")
print(f"Frequency   : {freq}MHz")


############################
#####     CLEAN-UP     #####
############################
# This should be at the end of the script
del comm
print('\n***** CLEAN UP *****')
print("COM port deleted\n")

import os
import sys
from time import sleep
from dubLibs import boardcom
from dubLibs import dubrovnik as du

print('********************************')
print('***** DUROVNIK TEST START *****')
print('********************************\n')

os.system('cls')  # clear terminal screen

print(sys.path)

# comm is a global variable (within this file)
defaultPort = 5
comm = boardcom.detect_ports(defaultPort)

##################################
#####        M A I N        ######
##################################

# ENTER System Parameters Here
vcc = 3.0
freq = 8          # chose 8 (8.25), 15 (14.67) or 30 (29.33)
pmon_id = '5'

# cmd(comm, 'freq ' + str(freq))
du.cmd(comm, 'freq ' + str(freq))
du.cmd(comm, 'dispmode w')

# Read board configuration and reset the chip
comm.send('config')
cfg = comm.response()
print(cfg)
config = cfg.split('\n')
partNumber = config[1].split('=')[1].split(' ')[1].upper()
voltage = config[2].split('=')[1].split(' ')[1].lower()

# the previous run may have left it at low voltage
comm.send('psset 0 ' + voltage)

# read_id(narg=2)                 # read device ID

print('\n ********** DAC, ADC TEST **********')
dacvals = ['7ff', '400', '200', '100']
# Dadcs = ['Dadc = 0x700', 'Dadc = 0x420', 'Dadc = 0x1e8', 'Dadc = 0xf0']
comm.send('muxset 1')  # Select the DAC and route it to the MUX output
i = 0
for dacval in dacvals:
    comm.send('dacset ' + dacval)
    comm.send('adcstart c8')    # configure ADC and start A/D conversion
    comm.send('adcread')        # read result of A/D conversion
    resp = comm.response()
    Dadc = resp.splitlines()[1].split()[2]
    adc = eval(Dadc)
    msg = '\tDAC=0x%s => ADC=%s ' % (dacval, Dadc)
    if adc < .975*int(dacval, 16) or adc > 1.025*int(dacval, 16):
        print(msg + '(incorrect ADC value)' + 'FAIL')
    else:
        print(msg + 'PASS')
    i += 1
# restore MUX setting to original, to pass CS# to the flash
comm.send('muxset 0')

print('\n ********** PMON TEST **********')
for pmon in range(8):
    du.pmon_cfg(comm, dev_id=pmon)

for pmon in range(8):
    pmon_id = str(pmon)
    pmon_str = 'pmon ' + pmon_id + ' start; timer start; delay 20000;' + \
               'timer stop; pmon ' + pmon_id + ' stop; pmon ' + pmon_id + ' calc'
    comm.send(pmon_str)
    resp = comm.response().splitlines()[1]
    # i_mA = resp.splitlines()[1].split(' ')[2]
    if resp != 'i2c error':
        i_mA = resp
        print('\tPMON %d: I = %s mA' % (pmon, i_mA.split()[2]))
    else:
        print('\tPMON %d: %s' % (pmon, resp))

print('\n ********** LED TEST **********')
led_dict = [{'gpio': '9', 'port': 'GPIO_AD_B1_02-LED_R', 'color': 'RGB LED: RED'},
            {'gpio': '10', 'port': 'GPIO_AD_B1_03-LED_G', 'color': 'RGB LED: BLUE'},
            {'gpio': '11', 'port': 'GPIO_AD_B1_04-LED_B', 'color': 'RGB LED: GREEN'},
            {'gpio': '12', 'port': 'GPIO_AD_B1_05-LED_1', 'color': 'LED: BLUE'},
            {'gpio': '13', 'port': 'GPIO_B1_04-LED_2', 'color': 'LED: GREEN'},
            {'gpio': '14', 'port': 'GPIO_B1_05-LED_3', 'color': 'LED: RED'}]

print('Turn LEDs off')
for item in led_dict:
    # print(item)
    comm.send('gpiocfg ' + item['gpio'] + ' o')
    comm.send('gpiowr ' + item['gpio'] + ' 1')
    print('\t%s OFF' % (item['color']))
    sleep(.3)

print('Turn LEDs on')
for item in led_dict:
    # print(item)
    comm.send('gpiocfg ' + item['gpio'] + ' o')
    comm.send('gpiowr ' + item['gpio'] + ' 0')
    print('\t%s ON' % (item['color']))
    sleep(.3)

print('\n ********** Device Program/Erase/Read Test **********')
if partNumber[0:2] == 'AT':          # device present
    print('Device %s present' % partNumber)
    print('VCC = %sV' % voltage)
    print('Read Status Registers:')
    if partNumber[2:4] == 'XP':   # global unprotect for EcoXiP
        comm.send('39 0')
        comm.send('6; 71 1 0')    # STSREG2[3:2]="00"
        comm.send('65 1; 65 2')   # status reg read
    else:
        comm.send('05; 35')
    resp = comm.response().split('\n')
    print('STSREG1: %s' % resp[1])
    print('STSREG2: %s' % resp[2])

    print('\n    Erasing block 0...')
    comm.send('6;20 0; wait 0')      # erase block 0
    print('    Reading...')
    comm.send('b 0 20')              # read some data
    resp = comm.response().split('\n')[1]
    print('\t%s' % resp)

    if 'ffffffff' in resp:
        print('DEVICE ERASED')

    # set up programming
    print('\n    Programming...')
    comm.send('pattern caba0000 1')
    comm.send('06; 02 0 20; wait 0')
    # read and compare 1st word
    print('    Reading...')
    comm.send('0b 0 20')
    resp = comm.response().split('\n')[1]
    print('\t%s' % resp)

    if 'caba0000' in resp:
        print('\nPROGRAM PASS')
        print('\nREAD PASS')
    else:
        print('\nPROGRAM/READ FAIL')

    print('\n    Erasing block 0...')
    comm.send('6;20 0; wait 0')      # erase block 0
    comm.send('0b 0 20')
    resp = comm.response().split('\n')[1]
    print('\t%s' % resp)

    if 'ffffffff' in resp:
        print('\nERASE PASS')
    else:
        print('\nERASE FAIL')

print('\n ********** V_ADJ TEST **********')
vmax = eval(voltage)
vstep = 6
for i in range(vstep-1):
    v = vmax - vmax/vstep*i
    if v >= 0.9:    # this is the minimum voltage of the LDO
        vf = format('%.3f' % v)
        cmd = 'psset 0 ' + vf
        comm.send(cmd)
        sleep(.2)
        input('Set voltage %.3fV --> Verify and press <Enter> to continue' % v)
comm.send('psset 0 ' + str(vmax))    # restore starting value

############################
#####     CLEAN-UP     #####
############################
del comm
print('\n***** CLEAN UP *****')
print("COM port deleted\n")
print('*******************************')
print('******** TEST FINISHED ********')
print('*******************************\n')

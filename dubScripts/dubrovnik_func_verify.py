import os
import sys
from time import sleep
from dubLibs import boardcom
from dubLibs import dubrovnik as du

print('********************************')
print('***** DUROVNIK TEST START *****')
print('********************************\n')

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
freq = 8   # chose 8 (8.25), 15 (14.67) or 30 (29.33)
pmon_id = '5'

du.cmd(comm, f'freq {freq}')
du.cmd(comm, 'dispmode w')

# Read board configuration and reset the chip
print(du.get_version(comm))
config = du.get_config(comm)
print(config)
partNumber = config['Part#'].upper()
voltage = config['Voltage']
min_dly = int(config['min meas time (us)'])

if partNumber == 'UNKNOWN':
    voltage = '1.8'  # don't go higher, it may damage the MCU VCC_SD input

# the previous run may have left it at low voltage
comm.send(f'psset 0 {voltage}')

# read_id(narg=2)                 # read device ID

print('\n ********** DAC, ADC TEST **********')
dacvals = ['7ff', '400', '200', '100']
# Dadcs = ['Dadc = 0x700', 'Dadc = 0x420', 'Dadc = 0x1e8', 'Dadc = 0xf0']
comm.send('muxset 1')  # Select the DAC and route it to the MUX output
i = 0
for dacval in dacvals:
    comm.send(f'dacset {dacval}')
    comm.send('adcstart c8')    # configure ADC and start A/D conversion
    comm.send('adcread')        # read result of A/D conversion
    resp = comm.response()
    Dadc = resp.splitlines()[1].split()[2]
    adc = eval(Dadc)
    msg = '\tDAC=0x%s => ADC=%s ' % (dacval, Dadc)
    dac = int(dacval, 16)  # convert it to int for comparison
    if .975 * dac < adc < 1.025 * dac:
        print(msg + 'PASS')
    else:
        print(msg + '(incorrect ADC value)' + 'FAIL')
    i += 1
# restore MUX setting to original, to pass CS# to the flash
comm.send('muxset 0')

print('\n ********** PMON TEST **********')
du.pmoncfg(comm, meas='iv')

for pmon in range(5):
    pmon_id = str(pmon)
    pmon_str = f'pmon {pmon_id} start; timer start; delay {1.2*min_dly}; timer stop; pmon {pmon_id} stop; pmon {pmon_id} calc'

    comm.send(pmon_str)
    resp = comm.response()
    i_v = resp.splitlines()[1].split(' ')
    curr = i_v[2]
    volt = i_v[6]
    if resp != 'i2c error':
        print(f'\tPMON {pmon}: {volt:5s} V, {curr:5s} mA')
    else:
        print(f'\tPMON {pmon}: {resp}')

print('\n ********** LED TEST **********')
led = [{'gpio': '9', 'port': 'GPIO_AD_B1_02-LED_R', 'color': 'RGB LED: RED'},
       {'gpio': '10', 'port': 'GPIO_AD_B1_03-LED_G', 'color': 'RGB LED: BLUE'},
       {'gpio': '11', 'port': 'GPIO_AD_B1_04-LED_B', 'color': 'RGB LED: GREEN'},
       {'gpio': '12', 'port': 'GPIO_AD_B1_05-LED_1', 'color': 'LED: BLUE'},
       {'gpio': '13', 'port': 'GPIO_B1_04-LED_2', 'color': 'LED: GREEN'},
       {'gpio': '14', 'port': 'GPIO_B1_05-LED_3', 'color': 'LED: RED'}]

print('Turn LEDs off')
for gpioNumber in led:
    # print(item)
    comm.send(f'gpiocfg {gpioNumber["gpio"]} o')
    comm.send(f'gpiowr {gpioNumber["gpio"]} 1')
    print(f'\t{gpioNumber["color"]} OFF')
    sleep(.3)

print('Turn LEDs on')
for gpioNumber in led:
    # print(item)
    comm.send(f'gpiocfg {gpioNumber["gpio"]} o')
    comm.send(f'gpiowr {gpioNumber["gpio"]} 0')
    print(f'\t{gpioNumber["color"]} ON')
    sleep(.3)

print('\n ********** Device Program/Erase/Read Test **********')
if partNumber[0:2] == 'AT':          # device present
    print(f'Device {partNumber} present')
    print(f'VCC = {voltage}V')
    print('Read Status Registers:')
    if partNumber[2:4] == 'XP':   # global unprotect for EcoXiP
        comm.send('39 0')
        comm.send('6; 71 1 0')    # STSREG2[3:2]="00"
        comm.send('65 1; 65 2')   # status reg read
    else:
        comm.send('05; 35')
    resp = comm.response().split('\n')
    print(f'STSREG1: {resp[1]}')
    print(f'STSREG2: {resp[2]}')

    print('\n    Erasing block 0...')
    comm.send('6;20 0; wait 0')      # erase block 0
    print('    Reading...')
    comm.send('b 0 20')              # read some data
    resp = comm.response().split('\n')[1]
    print(f'\t{resp}')

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
    print(f'\t{resp}')

    if 'caba0000' in resp:
        print('\nPROGRAM PASS')
        print('\nREAD PASS')
    else:
        print('\nPROGRAM/READ FAIL')

    print('\n    Erasing block 0...')
    comm.send('6;20 0; wait 0')      # erase block 0
    comm.send('0b 0 20')
    resp = comm.response().split('\n')[1]
    print(f'\t{resp}')

    if 'ffffffff' in resp:
        print('\nERASE PASS')
    else:
        print('\nERASE FAIL')

print('\n ********** V_ADJ TEST **********')
comm.send('pmoncfg meas v')

vmin = 0.9  # this is the minimum voltage of the LDO
vmax = eval(voltage)  # int(voltage)
step = 10
K = (vmax - vmin) / step
epsilon = .04  # max allowed voltage difference

comm.send('psset 0 0')  # turn off power supply
sleep(1)  # wait for caps discharge and voltage to drop

print('\tVset[V] Vmeas[V] Diff')
for i in range(step):
    v = vmax - K * i
    vset = format('%.3f' % v)
    cmd = f'psset 0 {vset}'
    comm.send(cmd)
    sleep(.5)  # may need time for voltage to stabilize
    comm.send('pmon 1 start; delay 100000; pmon 1 stop; pmon 1 calc')
    resp = comm.response()
    v_str = resp.split('\n')[1].split(' ')[2]  # extract voltage value
    vmeas = float(v_str)  # convert it into a float
    vdiff = (v - vmeas) * 1000
    if((v - epsilon) < vmeas < (v + epsilon)):  # is measured voltage in range?
        print(f'\t {v:.3f}   {vmeas:.3f} {vdiff:3.0f}mV  : PASS')
    else:
        print(f'\t {v:.3f}   {vmeas:.3f} {vdiff:3.0f}mV  : FAIL')

comm.send(f'psset 0 {vmax}')  # restore starting value

print('Turn LEDs off')
for gpioNumber in led:
    # print(item)
    comm.send(f'gpiocfg {gpioNumber["gpio"]} o')
    comm.send(f'gpiowr {gpioNumber["gpio"]} 1')
    print(f'\t{gpioNumber["color"]} OFF')

# ************************
# *****  Disconnect  *****
# ************************
comm.disconnect(connectedPort, echo=1)
print('*******************************')
print('******** TEST FINISHED ********')
print('*******************************\n')

import sys
from boardmon import Comm


def prtcomm():
    print(comm.response())


def extract_meas_in_ua(s):
    l = s.split("=")
    ll = l[1].split(" ")
    f = float(ll[1]) * 1000.0
    return f


def int16_to_hex_le(x):
    s = format(x, '04x')
    return s[2:4]+s[0:2]


print("*** Please follow these steps: ***")
print("1. Turn off the Dubrovnik power")
print("2. Empty the socket(s) associated with power domain(s)")
print("3. Make sure JP4 has pins 2-3 covered (VCC_ADJ connected)")
print("4. Turn on the Dubrovnik power")
print("5. Press Dubrovnik RESET button")
print("")

input("Press Enter when done")
print("")

board_connect = False
while not board_connect:
    commport = input("enter COM port (example: COM5):")
    try:
        board_connect = True
        comm = Comm(commport)
    except:
        board_connect = False
        print("*** Error while trying to connect to board - exiting ***")
        print("Please tery again")

print("Board connected successfully")
print("")

# Clear EEPROM parameter data structure
comm.send("write 0 0000;eepwr 0 2")
comm.disconnect()

print("*** Please press Dubrovnik RESET button one more time: ***")
input("Press Enter when done")
print("")

board_connect = False
while not board_connect:
    try:
        board_connect = True
        comm = Comm(commport)
    except:
        board_connect = False
        print("*** Error while trying to connect to board - exiting ***")
        print("Please tery again")

print("Board connected successfully")
print("")

num_meas = 5

bias_list = []

eep_str = "50410200"

cont = True
n_domains = 0
while cont:
    n_domains += 1
    bias_entry = [0, 0, 0]
    ok = False
    while not ok:
        domain_str = input(
            "Enter next power domain to be calibrated (example: 5 - SOIC socket): ")
        domain = int(domain_str)
        if domain >= 0 and domain <= 32:
            ok = True

    bias_entry[0] = domain

    print("calibrating...")

    meas_avg = 0.0
    for i in range(0, num_meas):
        comm.send("volt 1.6;delay 200000")
        comm.send("pmon " + str(domain) + " start;delay 100000;pmon " +
                  str(domain) + " stop;pmon " + str(domain) + " calc")
        s = comm.response(net=True)
        meas_ua = extract_meas_in_ua(s)
        meas_avg += meas_ua
    meas_avg = meas_avg / num_meas
    bias_entry[1] = round(meas_avg)

    meas_avg = 0.0
    for i in range(0, num_meas):
        comm.send("volt 3.6;delay 200000")
        comm.send("pmon " + str(domain) + " start;delay 100000;pmon " +
                  str(domain) + " stop;pmon " + str(domain) + " calc")
        s = comm.response(net=True)
        meas_ua = extract_meas_in_ua(s)
        meas_avg += meas_ua
    meas_avg = meas_avg / num_meas
    bias_entry[2] = round(meas_avg)

    bias_list.append(bias_entry)
    # print(bias_entry)

    ok = False
    while not ok:
        resp = input("Calibrate another domain? [y/n]: ")
        resp = resp.lower()
        if resp[0] == 'y':
            ok = True
        elif resp[0] == 'n':
            cont = False
            ok = True
        else:
            ok = False


print("calibration done, writing to EEPROM...")

eep_str += int16_to_hex_le(n_domains*6)
for i in range(0, n_domains):
    eep_str += int16_to_hex_le(bias_list[i][0])
    eep_str += int16_to_hex_le(bias_list[i][1])
    eep_str += int16_to_hex_le(bias_list[i][2])

# print(eep_str)
l = len(eep_str)
i = 0
while l > 0:
    if (l > 32):
        wsize = 32
    else:
        wsize = l
    comm.send("write 0 " + eep_str[i: i + wsize])
    # print(comm.response())
    comm.send("eepwr " + format(i // 2, 'x') + " " + format(wsize // 2, 'x'))
    # print(comm.response())
    i += wsize
    l -= wsize

comm.send("write 0 ffff")
comm.send("eepwr " + format(i // 2, 'x') + " 2")

print("Done")

import time
from dubLibs import boardcom

# *********************
# *****  Connect  *****
# *********************
comm = boardcom.BoardComm()   # create an instance of class BoardComm
connectedPort = comm.find_and_connect(echo=1)

print("Dump SFDP before patch")
comm.send("5a 0 100")
print(comm.response())

comm.send("c0")
comm.send("C2 01")
comm.send("F4 08")
comm.send("F6 80")
comm.send("C2 02")
comm.send("F8 00")

comm.send("06; 81 800; wait 0")
# comm.send("0b 800 100")
# print(comm.response())

# ATXP032
comm.send("write 00 53464450070103FC00070114280000FF")
comm.send("write 10 05000105780000FF8700011C8C0000FF")
comm.send("write 20 0A000104D40000FFFD208CFFFFFFFF01")
comm.send("write 30 0000000000000000EEFFFFFFFFFF0000")
comm.send("write 40 FFFF00000C200F5210D800FF904A4E01")
comm.send("write 50 80BF94E220610644D0B0D0B0F7A7D55C")
comm.send("write 60 000000FF82000040000000000000FC01")
comm.send("write 70 21001000000042620C0B008071716565")
comm.send("write 80 00E494DC000000000C57240000000000")
comm.send("write 90 8000000008D1FFC708D1FFC70005C480")
comm.send("write a0 0005C4810005C4A50005C4A5716503D0")
comm.send("write b0 000000009C0000008823599A00000086")
comm.send("write c0 00000000000000007165029300000000")
comm.send("write d0 71650297000006010000000088027104")
comm.send("write e0 0000000600000000716501D6716501D4")
comm.send("write f0 00000000716501D000003805FFFFFFFF")

comm.send("06; 02 800 100; wait 0")

comm.send("c1")
comm.send("c3 d0")

comm.send("jrst")
time.sleep(0.1)

print("Dump SFDP after patch")
comm.send("5a 0 100")
print(comm.response())

comm.send("cmp 0 100")
print(comm.response())

# comm.send('b 0 100')
# print(comm.response())

# ***********************************
# ***** Disconnect, Delete Port *****
# ***********************************
comm.disconnect(connectedPort, echo=1)
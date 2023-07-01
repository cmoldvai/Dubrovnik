# import os
# import math
from dubLibs import boardcom
from dubLibs import dubrovnik

comm = boardcom.BoardComm()   # create an instance of class BoardComm
connectedPort = comm.find_and_connect(echo=1)
du = dubrovnik.Dubrovnik()

comm.send('\r')

for j in range(5):
    for i in range(10):
        comm.send('rr ' + str(i))
        resp = comm.response(removeCmd=True, returnAsList=False)
        # print("resp len = " + str(len(resp)))
        print(resp)

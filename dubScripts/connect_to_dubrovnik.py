from dubLibs import boardcom
from dubLibs import dubrovnik as du

# ***************************
# *****     M A I N     *****
# ***************************

# ***** CONNECT *****
comm = boardcom.BoardComm()   # create an instance of class BoardComm
connectedPort = comm.find_and_connect(echo=1)


# ADD YOUR CODE HERE
# comm.send('b 0 100')
# print(comm.response())


# ***** DISCONNECT *****
comm.disconnect(connectedPort, echo=1)

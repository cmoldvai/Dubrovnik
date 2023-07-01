from dubLibs import boardcom
from dubLibs import dubrovnik

# ***** CONNECT *****
comm = boardcom.BoardComm()   # create an instance of class BoardComm
du = dubrovnik.Dubrovnik()

portList = comm.getPortList()
print(f'\nFound the following ports: {portList}\n')

# Loop through all found ports
for n, port in enumerate(portList):
    print('\n*******************************')
    connectedPort = comm.connect(port)      # connect to port
    print('\n  TestBench version : ', end='')  # print SW version
    ver = du.get_version(comm)
    config = du.get_config(comm)
    partNumber = du.get_part_number(comm)   # print the P/N of installed device
    print(f'  Installed device  : {partNumber}')
    print('*******************************')

    # ***** DISCONNECT *****
    comm.disconnect(connectedPort, echo=0)

# ***** used in a console application to prevent to window from closing
input('\nPress ENTER to exit')

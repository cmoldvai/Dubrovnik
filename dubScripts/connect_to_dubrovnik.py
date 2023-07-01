from dubLibs import boardcom
from dubLibs import dubrovnik

# ***************************
# *****     M A I N     *****
# ***************************

# ***** CONNECT *****
comm = boardcom.BoardComm()   # create an instance of class BoardComm
du = dubrovnik.Dubrovnik()

connectedPort = comm.find_and_connect(echo=1)

ver = du.get_version(comm)
# print(ver)

config = du.get_config(comm)
# print(config)

partNumber = du.get_part_number(comm)
print(partNumber)


# ADD YOUR CODE HERE

# comm.send('b 0 100')
# print(comm.response())

# erase_time = du.block_erase(comm, block_size=64, start_addr=0x10000, echo=0)
# print(f'Erase time: {erase_time}')

# t_wait = du.page_program(comm, start_addr=0x10025,
#  length=0x100, increment=1, echo=1)
# print(t_wait)
#
# du.read(comm, start_addr=0x10000, length=0x200, echo=0)


# ***** DISCONNECT *****
comm.disconnect(connectedPort, echo=1)

input('Press ENTER to exit')

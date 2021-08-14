import sys

from boardmon import Comm

def prtcomm():
	print(comm.response())


commport = sys.argv[1]
comm = Comm(commport, icpause=0.01)
#comm = Comm(commport)
print ("Opened commport", commport)

#flash_addr = 0x60000000 # RT1050 FlexSPI
flash_addr = 0x10000000 # STM32L5 OCTOSPI
flash_size = 0x400000

srec_filename = sys.argv[2]

srec_fh = open(srec_filename, 'r')

nbytes_cur_page = 0
prev_addr = 0xffffffff

for line in srec_fh:
	#print(line[:2], line[4:12])
	if line[:2] != "S3":
		continue
	addr = int(line[4:12], 16)
	if addr < flash_addr or addr >= flash_addr + flash_size:
		continue
	addr -= flash_addr
	if addr//256 != prev_addr//256:
		if nbytes_cur_page > 0:
			comm.send("06; 02 " + format(prev_addr - prev_addr%256, 'x') + " 100; wait")
			prtcomm()
		nbytes_cur_page = 0
	nbytes = (len(line) - 14) // 2
	nbytes_cur_page += nbytes
	offst = addr%256
	if (addr % 4096) == 0:
		comm.send("06; 39 " + format(addr, 'x'))
		prtcomm()
		comm.send("06; 20 " + format(addr, 'x') + "; wait")
		prtcomm()
	comm.send ("write " + format(offst, 'x') + ' ' + line[12:12+nbytes*2])
	prtcomm()
	prev_addr = addr

# reached end of file - program last page
if nbytes_cur_page > 0:
	comm.send("06; 02 " + format(prev_addr - prev_addr%256, 'x') + " 100; wait")
	prtcomm()

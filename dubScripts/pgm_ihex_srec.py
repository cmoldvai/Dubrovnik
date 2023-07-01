import sys
from dubLibs import boardcom
# from boardcom import Comm


def srec_file_loader(srec_filename):
    # opens srec_filename
    # reads it line by line
    # processes data lines which start with S1, S2, S3
    # finds gaps in the data a essentially breaking it to
    # a list of contiguous blocks
    # returns:
    # 1. a list of start addresses, one per contiguous block
    # 2. a list of matching binary arrays, holding the data
    # for each contiguous block
    try:
        fh = open(srec_filename, 'r')
    except FileNotFoundError:
        print("Error: file", srec_filename, "not found")
        exit()
    addr_list = []
    block_list = []
    next_addr = 0
    for line in fh:
        if line[:2] == "S1":
            nbytes = (int(line[2:4], 16) - 3)
            addr = int(line[4:8], 16)
            data_start = 8
        elif line[:2] == "S2":
            nbytes = (int(line[2:4], 16) - 4)
            addr = int(line[4:10], 16)
            data_start = 10
        elif line[:2] == "S3":
            nbytes = (int(line[2:4], 16) - 5)
            addr = int(line[4:12], 16)
            data_start = 12
        else:
            continue

        if addr > next_addr or addr == 0:
            block_list.append(b"")
            addr_list.append(addr)

        next_addr = addr + nbytes
        block_list[-1] += bytes.fromhex(line[data_start:data_start+(nbytes*2)])
    return (addr_list, block_list)


def ihex_file_loader(ihex_filename):
    # opens Intel-hex
    # reads it line by line
    # processes data lines with record types 00 and 04
    # finds gaps in the data a essentially breaking it to
    # a list of contiguous blocks
    # returns:
    # 1. a list of start addresses, one per contiguous block
    # 2. a list of matching binary arrays, holding the data
    # for each contiguous block
    try:
        fh = open(ihex_filename, 'r')
    except FileNotFoundError:
        print("Error: file", ihex_filename, "not found")
        exit()
    addr_list = []
    block_list = []
    next_addr = 0
    seg_addr = 0

    for line in fh:
        if line[0] != ":":
            print("Intel-hex format error")
            exit()
        elif line[7:9] == "04":
            seg_addr = int(line[9:13], 16) * 0x10000
            continue
        elif line[7:9] == "00":
            addr = int(line[3:7], 16) + seg_addr
            nbytes = int(line[1:3], 16)
        else:
            continue

        if addr > next_addr or addr == 0:
            block_list.append(b"")
            addr_list.append(addr)

        next_addr = addr + nbytes
        block_list[-1] += bytes.fromhex(line[9:9+(nbytes*2)])

    return (addr_list, block_list)


def write_buf_write(inp_arr, dsize):
    # Take a binary array and writes it to the test bench's write buffer.
    # The array is broken into chuncks of 16 bytes. A 'write' command
    # is sent to the test bench per chunk.
    offst = 0
    while offst < dsize:
        if dsize - offst >= 16:
            end_offst = offst + 16
        else:
            end_offst = dsize
        cmdstr = "write " + format(offst, 'x') + " "
        while offst < end_offst:
            cmdstr += format(inp_arr[offst], '02x')
            offst += 1
        # print(cmdstr)
        comm.send(cmdstr)


def data_program_and_verify(data_array, start_addr, do_verify):
    # gets data from the caller
    # passes data to TestBench
    # loads value into the write buffer
    # from there programs the chip

    idx = 0
    cnt = 0
    addr = start_addr
    end_addr = start_addr + len(data_array)
    page_size = 256
    # ready value for BUSY bit
    rv = '0'

    while addr < end_addr:
        page_end = addr - (addr % page_size) + page_size
        if page_end > end_addr:
            page_end = end_addr
        prog_size = page_end - addr
        write_buf_write(data_array[idx:idx+prog_size], prog_size)
        cmdstr = "06; 02 " + format(addr, 'x') + \
            " " + format(prog_size, 'x') + ";wait " + rv
        # print(cmdstr)
        comm.send(cmdstr)
        if do_verify:
            cmdstr = "0b " + format(addr, 'x') + " " + format(prog_size, 'x')
            comm.send(cmdstr)
            cmdstr = "cmp 0 " + format(prog_size, 'x')
            comm.send(cmdstr)
            cmp_result = comm.response(removeCmd=True, removePrompt=True)
            if not ('Equal!' in cmp_result):
                print("Verify failed: address=0x" + format(addr, 'x') +
                      ", address=" + format(addr, 'x'))
                print(cmp_result)
        addr = page_end
        idx += prog_size
        cnt += 1
        if cnt % 1000 == 0:
            print(str(cnt) + " pages")


'''
def data_verify(data_array, start_addr=0):
	idx = 0
	cnt = 0
	addr = start_addr
	end_addr = start_addr + len(data_array)
	page_size = 256
	while addr < end_addr:
		page_end = addr - (addr % page_size) + page_size
		if page_end > end_addr:
			page_end = end_addr
		read_size = page_end - addr
		write_buf_write(data_array[idx:idx+read_size], read_size)
		cmdstr = "0b " + format(addr, 'x') + " " + format(read_size, 'x')
		#print(cmdstr)
		comm.send(cmdstr)
		cmdstr = "cmp 0 " + format(read_size, 'x')
		comm.send(cmdstr)
		cmp_result = comm.response(net=True)
		#print(cmp_result)
		if cmp_result[0:6] != "equal!":
			print("Verify failed: address=0x" + format(addr, 'x') + ", address=" + format(addr, 'x'))
			print(cmp_result)
		addr = page_end
		idx += read_size
'''

commport = sys.argv[1]
# comm = Comm(commport)
comm = boardcom.BoardComm()  # create an instance of class BoardComm

comm.connect(commport)

comm.send('psset 0 0; delay 3000000')
comm.send('psset 0 3.3; delay 1000000')
comm.send('freq 3')
comm.send('setpart at25sf128a')
comm.send('9f 3')
print(comm.response(removeCmd=True))

flash_base_addr = 0

hex_filename = sys.argv[2]

print('Loading Hex File...')
ihex = ihex_file_loader(hex_filename)
'''
for ad in ihex[0]:
	print(format(ad, 'x'))
for ba in ihex[1]:
	for b in ba:
		print(format(b, '02x') + " ", end="")
	print("")
'''
comm.send("echo off")
i = 0
for ad in ihex[0]:
    print("processing block address 0x" + format(ad, 'x') +
          ", size 0x" + format(len(ihex[1][i]), 'x'))
    print("programing and verifying...")
    data_program_and_verify(ihex[1][i], ad, True)
    print("done")
    i += 1

comm.send("echo on")

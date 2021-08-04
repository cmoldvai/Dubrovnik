from dubLibs import boardcom
# import sys

pageSize = 0x100
led_dict = {'r1': '9', 'g1': '11', 'b1': '10',
            'r2': '14', 'g2': '13', 'b2': '12'}


def version(comm):
    ver = cmd(comm, 'ver')
    return ver


def dispmode(comm, mode='b'):
    """
    The function requires 1 input arguments,
        comm : The handle to the comm port to communicate with the Dubrovnik board
        mode : 'b' for the byte, 'w' for double-word
    """
    comm.send('dispmode ' + mode)
    return None


def cmd(comm, cmdstr, echo=0):
    """
    Sends a command string (cmdstr) to dubrovnik on comm
    If echo=1 it will print the response on the terminal
    """
    comm.send(cmdstr)
    if echo == 1:
        print(comm.response())
        return(comm.response())


def update_byte(old_byte, mask, data):
    new_byte = (old_byte & ~mask) | (data & mask)
    return new_byte


def tohex(num):
    """
    Takes an integer and returns the hex string representation of 
    the least significant byte (with leading zeros)
    Parameters:   
        num : unsigned integer value to change to string (1 byte)
    Examples:
        print(tohex(0x3)
        out: '03'
    """

    if type(num) is int:
        bs = format(num, "02x")
    elif type(num) is str:
        if 'x' in num:
            bs = num.split('x')[-1]
        else:
            bs = num
    else:
        try:
            bs = format(int(num), "02x")
        except Exception:
            bs = format(int(num, 16), "02x")
    return bs


def get_wait_time(comm):
    comm.send('dvar wait_time')
    return (comm.response())


# TODO: REVIEW use Eyal's version with page boundaries
def page_program(comm, start_addr=0, nbyte=0, pattern='cafe0000',
                 increment='0'):
    opcode = '02'
    wel = '06;'
    cmdstr = f'pattern {pattern} {increment}'
    comm.send(cmdstr)
    cmdstr = f'{wel} {opcode} {start_addr:x} {nbyte:x}; wait 0'
    comm.send(cmdstr)


def pattern_program(comm, start_addr=0, end_addr=0, pattern='cafe0000',
                    increment='0', echo=0):
    cmdstr = f'pattern {pattern} {increment}'
    comm.send(cmdstr)
    opcode = '02'
    wel = '06'
    # pageSize = 0x100
    addr = start_addr
    while addr < end_addr:
        pageEnd = addr - (addr % pageSize) + pageSize
        if pageEnd > end_addr:
            pageEnd = end_addr
        progSize = pageEnd - addr
        cmdstr = f'{wel}; {opcode} {addr:x} {progSize:x}; wait 0'
        if echo == 1:
            print(cmdstr)
        comm.send(cmdstr)
        addr = pageEnd


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


def file_loader(datafile):
    # opens filename
    # reads it into a binary array
    # converts it into a specific format
    # returns the binary array
    try:
        fh = open(datafile, 'rb')
    except FileNotFoundError:
        print("Error: file", datafile, "not found")
        exit()

    data_array = fh.read()
    return data_array


def write_buf_write(comm, inp_arr, dsize):
    # takes an input binary array
    # loads the data from the binary array into the
    # test bench write buffer using a sequence of 'write' commands
    offst = 0
    while offst < dsize:
        if dsize - offst >= 16:
            end_offst = offst + 16
        else:
            end_offst = dsize
        # cmdstr = "write " + format(offst, 'x') + " "
        cmdstr = f'write {offst:x} '
        while offst < end_offst:
            # cmdstr += format(inp_arr[offst], '02x')
            cmdstr += f'{inp_arr[offst]:02x}'
            offst += 1
        comm.send(cmdstr)


def data_program(comm, data_array, start_addr=0):
    # gets a binary data array from the caller
    # programs binary data page by page
    # first writing the page data into the test bench write buffer
    # then performing a test bench program operation
    idx = 0
    addr = start_addr
    end_addr = start_addr + len(data_array)
    while addr < end_addr:
        pageEnd = addr - (addr % pageSize) + pageSize
        if pageEnd > end_addr:
            pageEnd = end_addr
        progSize = pageEnd - addr
        # cmdstr = write_buf_write(comm, data_array[idx:idx+progSize], progSize)
        write_buf_write(comm, data_array[idx:idx+progSize], progSize)
        # cmdstr = "06;02 " + format(addr, 'x') + " " + format(progSize, 'x') + ";wait 0"
        cmdstr = f'06;02 {addr:x} {progSize:x};wait 0'
        comm.send(cmdstr)
        addr = pageEnd


def block_erase(comm, block_size=4, start_addr=0, num_blocks=1,
                trig=False, echo=0):
    wel = '06'
    blockSizeKB = block_size * 1024
    startAddr = (start_addr // blockSizeKB) * blockSizeKB
    # print(startAddr)
    if block_size == 4:
        opcode = '20'
    elif block_size == 32:
        opcode = '52'
    elif block_size == 64:
        opcode = 'd8'
    else:
        raise ValueError("Incorrect block size")
    addr = startAddr
    for n in range(0, num_blocks):
        if trig:
            cmdstr = f'{wel}; trig 1;{opcode} {addr:x}; wait 0; trig 0'
            # print(cmdstr)
        else:
            cmdstr = f'{wel}; {opcode} {addr:x}; wait 0'
            # print(cmdstr)
        comm.send(cmdstr)
        if echo == 1:
            print(comm.response())
        addr += blockSizeKB
    return 0


def read(comm, opcode='0b', staddr=0, length=256, echo=1):
    cmdstr = f'{opcode} {staddr:x} {length:x}'
    comm.send(cmdstr)
    if echo == 1:
        print(comm.response())


def read_id(comm, opcode='9f ', narg=2, echo=1):
    comm.send(opcode + str(narg))
    if echo == 1:
        print(comm.response())


def pmon_calib(comm, domain):
    pmoncfg(comm, avg=4, vbt=140, vst=2116, mode='sht', meas='i')
    cmdstr = f'pmon {domain} start; delay 100000; pmon {domain} stop; pmon {domain} calc'
    comm.send(cmdstr)
    resp = comm.response()
    print(resp)
    ibias = resp.split('\n')[1].split(' ')[-2]
    ibias_uA = int(1000 * float(ibias))
    ibias = str(ibias_uA)
    # print(ibias)
    # print(ibias_uA)
    addr = int(domain) * 2
    cmdstr = f'write {addr:x} {ibias_uA}'
    comm.send(cmdstr)
    print(comm.response())
    comm.send('dispmode b')
    comm.send('dump w 0 10')
    print(comm.response())
    comm.send('eepwr {addr} 2')
    comm.send('eeprd 0 10')
    print(comm.response())


def pmoncfg(comm, avg=None, vbt=None, vst=None, mode=None, meas=None):
    # def pmoncfg(comm, avg=4, vbt=140, vst=2116, mode='sht', meas='i'):
    """
    Syntax      : pmoncfg <category> <value>
    Description : Configures the INA230 power monitor
        id   : deviceID [1-31]
        avg  : number of averages
               [1 4 16 64 128 256 512 1024]
        vbt  : bus voltage conversion time [us]
               [140 204 332 588 1100 2116 4156 8244]
        vst  : shunt voltage conversion time [us]
               [140 204 332 588 1100 2116 4156 8244]
        meas : measurement subject
               i (current)
               v (voltage)
               iv (current and voltage)
               p (power)
        mode : svt (shunt voltage triggered)
               bvt (bus voltage triggered)
               sbt (shunt and bus triggered)
               svc (shunt voltage continuous)
               bvc (bus voltage continuous)
               sbc (shunt and bus continuous)
    """
    # print(avg, vbt, vst, mode, meas)

    # if dev_id == None:
    #     print('ERROR!!! Must specify deviceID')
    #     return -1

    if avg is not None:
        cmdstr = f'pmoncfg avg {avg}'
        comm.send(cmdstr)

    if vbt is not None:
        cmdstr = f'pmoncfg vbt {vbt}'
        comm.send(cmdstr)

    if vst is not None:
        cmdstr = f'pmoncfg vst {vst}'
        comm.send(cmdstr)

    if mode is not None:
        cmdstr = f'pmoncfg mode {mode}'
        comm.send(cmdstr)

    if meas is not None:
        cmdstr = f'pmoncfg meas {meas}'
        comm.send(cmdstr)


# def led(comm, led_id, on=False):
#     comm.send(cmd_str)


def echo(comm, onoff):
    """This function will turn the echo on/off for dubrovnik
    Parameters:
        The function requires 2 input arguments,
        comm  : The handle to the comm port to communicate with the Dubrovnik board
        onoff : 'on' or 'off' to set the echo
    The function has no return value
    """

    if onoff.lower() in ['on', 'off']:
        comm.send("echo " + onoff)
    else:
        print('Echo variable onoff must be "on" or "off".')
    return None


def set_spi_mode(spi_mode):
    if spi_mode == 'spi':
        # READ OpCode in SPI: 03 (legacy), 0B (fast read)
        return '0B'
    elif spi_mode == 'q114':
        return '6B'                 # READ OpCode in QSPI 1-1-4
    elif spi_mode == 'q144':
        return 'eb'                 # READ OpCode in QSPI 1-4-4
    elif spi_mode == 'q044':
        return 'ebc'
    elif spi_mode == 'qpi':
        pass
    else:
        pass


def wr_buffer(comm, spi_mode):
    # 0x0000: 'aaaa'
    # 0x4000: '0000'
    # 0x8000: 'ffff'
    # 0xC000: 'f0f0'
    # 0x10000:'ff00'
    if spi_mode == 'spi':            # spi mode
        pattern = 'aaaaaaaa'
        start_addr = 0x0000
    elif spi_mode[0].lower() == 'q':  # quad mode
        pattern = 'f0f0f0f0'
        start_addr = 0xC000
    elif spi_mode[0].lower() == 'o':  # octal mode
        pattern = 'ff00ff00'
        start_addr = 0x10000
    else:
        pattern = 'caba0000'
        start_addr = 0x20000
    comm.send('pattern ' + pattern + ' 0')
    return start_addr


def flash_program(comm):
    print('******************************')
    print('  Program Flash with Pattern  ')
    print('******************************')
    print('0x0000 : "aaaaaaaa"')
    print('0x4000 : "00000000"')
    print('0x8000 : "ffffffff"')
    print('0xc000 : "f0f0f0f0"')
    print('0x10000: "ff00ff00"')
    print('Start programming ')
    # Blocks of N * nbyte are programmed with a sellected pattn
    N = 0x40  # 0x40 * 0x100 = 64 * 256 = 16KB
    base = 0
    end_addr = base + N * pageSize
    print(hex(base))
    pattn = 'aaaaaaaa'
    incr = '0'
    pattern_program(comm, start_addr=base, end_addr=end_addr,
                    pattern=pattn, increment=incr)

    base = base + N * 0x100
    end_addr = base + N * pageSize
    print(hex(base))
    pattn = '00000000'
    incr = '0'
    pattern_program(comm, start_addr=base, end_addr=end_addr,
                    pattern=pattn, increment=incr)

    base = base + N * 0x100
    end_addr = base + N * pageSize
    print(hex(base))
    pattn = 'ffffffff'
    incr = '0'
    pattern_program(comm, start_addr=base, end_addr=end_addr,
                    pattern=pattn, increment=incr)

    base = base + N * 0x100
    end_addr = base + N * pageSize
    print(hex(base))
    pattn = 'f0f0f0f0'
    incr = '0'
    pattern_program(comm, start_addr=base, end_addr=end_addr,
                    pattern=pattn, increment=incr)

    base = base + N * 0x100
    end_addr = base + N * pageSize
    print(hex(base))
    pattn = 'ff00ff00'
    incr = '0'
    pattern_program(comm, start_addr=base, end_addr=end_addr,
                    pattern=pattn, increment=incr)

    print('*********************')
    print('  Verify Program     ')
    print('*********************')
    # Read 2 pages at addresses in increments of 0x4000
    for i in range(0, 6):
        base = 0x4000 * i
        for j in range(0, 2):
            addr = base + 256 * j
            read(comm, opcode='b', staddr=addr, length=0x100)


if __name__ == '__main__':
    # ***** Connect
    comm = boardcom.BoardComm()
    comPort = comm.find_and_connect(echo=1)

    block_erase(comm, echo=1)
    wait_time = get_wait_time(comm)
    print(wait_time)

    data_array = file_loader(r'C:\MyLibs\Dubrovnik\dubScripts\Tesla.bin')
    # print(df)
    dsize = len(data_array)
    # write_buf_write(comm, data_array, dsize)
    # data_program(comm, data_array, start_addr=0)
    read(comm, length=dsize)

    # ***** Disconnect
    comm.disconnect(comPort, echo=1)

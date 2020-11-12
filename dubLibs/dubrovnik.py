# from dubLibs import boardcom
import sys
# import boardcom as comm

pageSize = 0x100


def page_program(comm, start_addr=0, nbyte=0, pattern='caba0000', increment='0'):
    opcode = '02'
    wel = '06;'
    cmd = f'pattern {pattern} {increment}'
    comm.send(cmd)
    cmd = f'{wel} {opcode} {start_addr:x} {nbyte:x}; wait 0'
    # cmd = wel + " " + opcode + " " + start_addr + " " + nbyte + "; wait 0"
    comm.send(cmd)


def pattern_program(comm, start_addr=0, end_addr=0, pattern='caba0000', increment='0'):
    cmd = f'pattern {pattern} {increment}'
    comm.send(cmd)
    opcode = '02'
    wel = '06'
    pageSize = 0x100
    addr = start_addr
    while addr < end_addr:
        pageEnd = addr - (addr % pageSize) + pageSize
        if pageEnd > end_addr:
            pageEnd = end_addr
        progSize = pageEnd - addr
        cmd = f'{wel}; {opcode} {addr:x} {progSize:x}; wait 0'
        print(cmd)
        comm.send(cmd)
        addr = pageEnd


def data_program(comm, start_addr=0, end_addr=0):
    opcode = '02'
    wel = '06'
    pageSize = 0x100
    addr = start_addr
    while addr < end_addr:
        pageEnd = addr - (addr % pageSize) + pageSize
        if pageEnd > end_addr:
            pageEnd = end_addr
        progSize = pageEnd - addr
        cmd = f'{wel}; {opcode} {addr:x} {progSize:x}; wait 0'
        comm.send(cmd)
        addr = pageEnd


def block_erase(comm, block_size=4, start_addr=0, num_blocks=1, trig=False, echo=0):
    wel = '06'
    kB = 0x400
    blockSizeKB = block_size * kB
    mask = ~(blockSizeKB - 1)    # pay attention: tricky
    startAddr = start_addr & mask
    print(f'{startAddr:x}')

    if block_size == 4:
        opcode = '20'
    elif block_size == 32:
        opcode = '52'
    elif block_size == 64:
        opcode = 'D8'
    else:
        print('Invalid block size')
        return -1

    addr = startAddr
    for n in range(0, num_blocks):
        if trig == True:
            cmd = f'{wel}; trig 1;{opcode} {addr:x}; wait 0; trig 0'
            # print(cmd)
        else:
            cmd = f'{wel}; {opcode} {addr:x}; wait 0'
            print(cmd)
        comm.send(cmd)
        if echo == 1:
            print(comm.response())
        addr += blockSizeKB
    return 0


def read(comm, opcode="0b", staddr="00", nbyte="100", echo=1):
    cmd = opcode + " " + staddr + " " + nbyte
    comm.send(cmd)
    if echo == 1:
        print(comm.response())


def read_id(comm, opcode="9f ", narg=2, echo=1):
    comm.send(opcode + str(narg))
    if echo == 1:
        print(comm.response())


def pmon_cfg(comm, dev_id=0, reset=0, avg=1, bus_tconv=0, shunt_tconv=5, mode=5):
    """
    :param dev_id: # INA230 channels: 0 to 6
    :param avg: 0=1, 1=4, 2=16, 3=64, 4=128, 5 256, 6=512, 7=1024
    :param bus_tconv:    0=140us, 1=204us, 2=332us, 3=588us
                        4=1.1ms, 5=2.116ms, 6=4.156ms, 7=8.244ms
    :param shunt_tconv:    0=140us, 1=204us, 2=332us, 3=588us
                        4=1.1ms, 5=2.116ms, 6=4.156ms, 7=8.244ms
    :param mode: 0=pwr down, 1=shunt.trig 2=bus.trig 3=shunt and bus trig
                 4=pwr down, 5=shunt.cont 6=bus.cont 7=shunt and bus cont
    """
    rst = reset * 0x8000
    if avg <= 7:
        val1 = 512 * avg
        # print('val1 = ' + str(val1))
    else:
        print('avg must be between 0 and 7')
    if bus_tconv <= 7:
        val2 = 64 * bus_tconv
        # print('val2 = ' + str(val2))
    else:
        print('Bus Conversion Time must be between 0 and 7')
    if shunt_tconv <= 7:
        val3 = 8 * shunt_tconv
        # print('val3 = ' + str(val3))
    else:
        print('Shunt Conversion Time must be between 0 and 7')
    if mode <= 7:
        val4 = mode
        # print('val4 = ' + str(val4))
    else:
        print('MODE must be between 0 and 7')

    val = rst + val1 + val2 + val3 + val4
    # print('val = ' + str(val))
    val = format(val, 'X')
    # cmd = rst + '100' + avg + bus_tconv + shunt_tconv + mode
    cmd = val
    # print(cmd)
    cmd = 'pmoncfg ' + str(dev_id) + ' ' + cmd
    comm.send(cmd)
    # resp = comm.response()
    # print(resp.splitlines()[0])


def cmd(comm, cmd_str, echo=0):
    comm.send(cmd_str)
    if echo == 1:
        print(comm.response())
        return(comm.response())


def set_mode(spi_mode):
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
    prog_str = ''
    # Blocks of N * nbyte are programmed with a sellected pattn
    N = 0x40  # 0x40 * 0x100 = 64 * 256 = 16KB
    pattn = 'aaaaaaaa 0'
    base = 0
    print(hex(base))
    for i in range(N):
        addr = format(base + 0x100 * i, 'X')
        page_program(comm, start_addr=addr, nbyte='100', pattern=pattn)

    base = base + N * 0x100
    print(hex(base))
    pattn = '00000000 0'
    for i in range(N):
        addr = format(base + 0x100 * i, 'X')
        page_program(comm, start_addr=addr, nbyte='100', pattern=pattn)

    base = base + N * 0x100
    print(hex(base))
    pattn = 'ffffffff 0'
    for i in range(N):
        addr = format(base + 0x100 * i, 'X')
        page_program(comm, start_addr=addr, nbyte='100', pattern=pattn)

    base = base + N * 0x100
    print(hex(base))
    pattn = 'f0f0f0f0 0'
    for i in range(N):
        addr = format(base + 0x100 * i, 'X')
        page_program(comm, start_addr=addr, nbyte='100', pattern=pattn)

    base = base + N * 0x100
    print(hex(base))
    pattn = 'ff00ff00 0'
    for i in range(N):
        addr = format(base + 0x100 * i, 'X')
        page_program(comm, start_addr=addr, nbyte='100', pattern=pattn)

    print('*********************')
    print('  Verify Program     ')
    print('*********************')
    # Read 2 pages at addresses in increments of 0x4000
    for i in range(0, 6):
        base = 0x4000 * i
        for j in range(0, 2):
            addr = format(base + 256 * j, 'X')
            read(comm, opcode='b', staddr=addr, nbyte='100')


def erase_memory_block(comm, num_blocks=16, block_size=4):
    print('*********************')
    print('     BLOCK ERASE     ')
    print('*********************')
    # Erase the BLOCKS that will be used in the experiment

    num_blocks = 16     # Number of blocks to be erased
    block_size = 4      # 4KB block size

    print('Starting block erase\n')
    for i in range(0, num_blocks + 1):
        bl_start_addr = format(block_size * 1024 * i, 'X')
        print(bl_start_addr)
        block_erase(comm, block_size=4, start_addr=bl_start_addr, trig=False)

    print('Block erase DONE\n')
    # cmd('delay 100000')
    cmd(comm, 'delay 5000')

    # VERIFY if device was erased
    print('Verify blocks erased')

    for i in range(0, 2):
        addr = format(256 * i, 'X')
        read(comm, opcode='b', staddr=addr, nbyte='100')


if __name__ == "__main__":
    cmd('9f 2')

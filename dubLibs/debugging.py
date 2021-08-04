from dubLibs import boardcom
from dubLibs import dubrovnik as du
import pandas as pd
import matplotlib.pyplot as plt

# from helper_functions import tohex
# from helper_functions import update_byte


# ***************************
# ***** Enter Test Mode *****
# ***************************
def tm_enter(comm):
    """
    This function will send the "c0" command to the DUT, to enter the test-mode.
    TestBench automatically configures the MUX on Dubrovnik to set 10V on CS
    Parameters:
    The function has one input arguments
     comm: The handle to the comm port to communicate with the Dubrovnik board
    """
    # Enter Test-mode
    comm.send("c0")
    # print("entered test mode...")


# **************************
# ***** Exit Test Mode *****
# **************************
def tm_exit(comm):
    """
    This function will send the "c3 d0" command to the DUT, to exit the test-mode.
    TestBench automatically restores the CS signal
    Parameters:
    The function has one input arguments
     comm : The handle to the comm port to communicate with the Dubrovnik board
    """
    # Exit test-mode
    comm.send("c3 d0")
    # print("exited test mode.")


# ******************************
# ***** Read test register *****
# ******************************
def rd_test_reg(comm, addr=0, tm_enterexit=False):
    """
    This function will read to the test register
    Parameters
    The function requires 3 input arguments,
     comm         : The handle to the comm port to communicate with the Dubrovnik board
     addr         : The test register address to read as a string
     tm_enterexit : If True, will enter before and exit after rd
    The function returns the hex string read from the dubrovnik
    ---------
    Examples:
    rd_test_reg(comm=comm, addr=0x81)
    rd_test_reg(comm=comm, addr=0x03)
    """

    if tm_enterexit:
        tm_enter(comm)
    cmdstr = f"c6 {addr:x}"
    # cmdstr = "c6 " + tohex(addr)
    try:
        data = commtxrx(comm, cmdstr).split(' ')[0]
    except Exception:
        data = None
    if tm_enterexit:
        tm_exit(comm)
    return data


# *******************************
# ***** Write test register *****
# *******************************
def wr_test_reg(comm, addr, data, rmw=False, mask=0xff, tm_enterexit=False):
    """
    This function will write to the test register
    Parameters:
        The function requires 3 input arguments:
        comm         : The handle to the comm port to communicate with the Dubrovnik board
        addr         : The test regiter address to write as a string
        data         : The data to write as a string
        rmw          : If True, the funcion will only write bits where mask is 1
                    and will return the old data, 
                    otherwise the return is None
        mask         : What bits to write if rmw=True
        tm_enterexit : If True, will enter before and exit after wr

    The function returns the old_data if RMW, otherwise None
    --------
    Examples:
    wr_test_reg(comm=comm, addr=0x81, data=0x02)
    wr_test_reg(comm=comm, addr=0x01, data=0x50, rmw=True, mask=0x50)
    """
    if tm_enterexit:
        tm_enter(comm)
    if rmw:
        old_data = int(rd_test_reg(comm=comm, addr=addr), 16)
        new_data = update_byte(old_data, mask, data)
    else:
        new_data = data
        old_data = None
    # cmdstr = "c5 " + tohex(addr) + " " + tohex(new_data) # CM
    cmdstr = f"c5 {addr:02x} {new_data:02x}"  # CM
    comm.send(cmdstr)

    if tm_enterexit:
        tm_exit(comm)
    return old_data


# ******************************
# *****     Update byte    *****
# ******************************
def update_byte(old_byte, mask, data):
    new_byte = (old_byte & ~mask) | (data & mask)
    return new_byte


def commtxrx(comm, cmdstr, stripspace=False, joinlines=True):
    """
    This function will send the cmdstr to the Dubrovnik board,
    and then gather the response back from the board.
    The response string is then parsed to remove the cmdstr.
    Parameters:
    -----------
    The function has three input arguments
     comm:       The handle to the comm port to communicate with the Dubrovnik
                 board
     cmdstr:     The command string that is sent to the Dubrovnik board
     stripspace: If this input is set to True, then all spaces in the return
                 string from the Dubrovnik board are deleted.
     Examples:
     ---------
     In [3]: fhd.commtxrx(comm=comm, cmdstr='0b 0 10', stripspace=False)
     Out[3]: 'ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff'

     In [4]: fhd.commtxrx(comm=comm, cmdstr='0b 0 10', stripspace=True)
     Out[4]: 'ffffffffffffffffffffffffffffffff'
    """

    cmdstr = cmdstr.lower()
    comm.send(cmdstr)
    resp = comm.response()
    # remove the cmdstr in the response
    resp = resp.replace(cmdstr, "", 1)
    # remove the '>>>' response marker
    resp = resp.replace(">", "")
    # if joinlines is True, then join all lines into a single string
    if joinlines is True:
        resp = "".join(resp.splitlines())
    # if stripspace == True, remove any spaces
    if stripspace is True:
        resp = resp.replace(" ", "")
    # remove any leading and trailing spaces
    resp = resp.strip()
    return resp


# *********************************************
# *****   get Vt distribution curves    *******
# *********************************************
def get_vt_curves(comm, addr=0, numbytes=0x100, prefix="", fast=True, nocpsum=False,
                  minvdac=0, maxvdac=63, with_nbias=True, plot=False):
    """
    This function will get the Vt distribution curve
    Parameters:
    The function requires 4 input arguments,
     comm     : The handle to the comm port to communicate with the Dubrovnik board
     addr     : This is the start byte address of the region
     numbytes : This is the number of bytes in the region
     prefix   : The string which will be added to the prefix column
     fast     : If this boolean input is False, then the function will
                read back the data from the DUT back to the PC.
                If this boolean input is True, then the function will
                not read back the data from the DUT back to the PC.
     minvdac  : This is the minumum value used in the VDAC during the
                FDMA read. Default is 0.
     maxvdac  : This is the maximum value used in the VDAC during the
                FDMA read. Default is 63.

    The function will return a dataframe with the following columns
     prefix     : This will contain the prefix string
     addr       : This will contain the start byte address
     vt         : The vt voltage
     csum       : The cumulative number of 1's at the vt voltage
     psum       : The number of 1's at the vt voltage
     hexstring  : The raw hex read data at the vt voltage
     with_nbias : Turns on ERS_MODE if True
    --------
    Examples
    dbg.get_vt_curves(comm=comm, addr=0x0, numbytes=0x100, prefix='a', fast=True)
    """

    print("# Inside fdma with addr:%x" % addr + " , numbytes:%x" %
          numbytes + " , prefix: " + prefix)

    # check for valid selections for minvdac and maxvdac
    if (minvdac > 64) | (minvdac < 0):
        myminvdac = 0
    else:
        myminvdac = minvdac
    if (maxvdac > 64) | (maxvdac < 0):
        mymaxvdac = 64
    else:
        mymaxvdac = maxvdac + 1
    if myminvdac > mymaxvdac:
        myminvdac = mymaxvdac
    # Enable test-mode
    tm_enter(comm)
    # Save initial value of TL 0x81, 0x89, 0x8e
    du.echo(comm, 'on')
    # Set TL_ANALOG_ON to 1
    initval_81 = wr_test_reg(comm, addr=0x81, data=0x02, mask=0x02, rmw=True)
    # Set VDAC_EN to 1
    initval_89 = wr_test_reg(comm, addr=0x89, data=0x80, mask=0x80, rmw=True)
    # Set TL_ERS_MODE to 1 if with_nbias is True
    if with_nbias:
        initval_8E = wr_test_reg(comm, addr=0x8E, data=0x04,
                                 mask=0x08, rmw=True)

    if fast is True:
        du.echo(comm, 'off')

    ret_list = []
    prev_psum = 0
    for myvref in range(myminvdac, mymaxvdac):
        # print("# change TL_VDAC[5:0] to %0x"%myvref)
        wr_test_reg(comm, addr=0x89, data=(myvref | 0x80))
        # set rdcnt to numbytes, and do a while loop till rdcnt is less than
        # 0x1000
        rdcnt = numbytes
        rdaddr = addr
        hexstring = ""
        cumsum = 0
        while rdcnt > 0x1000:
            # print("# read 0x1000 bytes the data from %x"%rdaddr)
            comstr = f"0b {rdaddr:x} 1000"
            # comstr = "0b " + tohex(rdaddr) + " 1000"
            rdhexstr = commtxrx(comm, comstr, stripspace=True)
            if fast is True:
                retstr = commtxrx(comm=comm, cmdstr="count1 1000")
                # print("# count1 gives " + retstr)
                cumsum = cumsum + int(retstr, 16)
            else:
                hexstring = hexstring + rdhexstr

            rdaddr = rdaddr + 0x1000
            rdcnt = rdcnt - 0x1000
        # now check if rdcnt is > 0, then we still have some bytes to do
        if rdcnt > 0:
            # print("# read %0x"%rdcnt + " bytes the data from %x"%rdaddr)
            if fast is True:
                comstr = f"0b {rdaddr:x} {rdcnt:x}"
                # comstr = "0b " + tohex(rdaddr) + " " + tohex(rdcnt)
                rdhexstr = commtxrx(comm, comstr)
                retstr = commtxrx(comm=comm, cmdstr=f"count1 {rdcnt:x}")
                # retstr = commtxrx(comm=comm, cmdstr="count1 " + tohex(rdcnt))
                # print("# count1 gives " + retstr)
                cumsum = cumsum + int(retstr, 16)
            else:
                comstr = f"0b {rdaddr:x} {rdcnt:x}"
                # comstr = "0b " + tohex(rdaddr) + " " + tohex(rdcnt)
                rdhexstr = commtxrx(comm, comstr, stripspace=True)
                hexstring = hexstring + rdhexstr

        if fast is False:
            # convert the hextring into a binary string and count the number
            # of 1s
            if nocpsum is True:
                cumsum = 0
            else:
                cumsum = format(int(hexstring, 16), 'b').count("1")

        # For PDF, then subtract prev_csum
        if cumsum > prev_psum:
            curr_psum = cumsum - prev_psum
        else:
            curr_psum = 0
        prev_psum = cumsum
        # calculate the vt based on the formula,
        #   vt = 2.000 + (0.125 * index)
        vt = 2.000 + (0.125 * myvref)
        if fast is False:
            ret_list.append([prefix, vt, cumsum, curr_psum, hexstring])
        else:
            ret_list.append([prefix, vt, cumsum, curr_psum])

    # add the last bin
    prev_psum = cumsum
    cumsum = numbytes * 8
    curr_psum = cumsum - prev_psum
    vt = 2 + 0.125 * (maxvdac + 1)
    if fast is True:
        ret_list.append([prefix, vt, cumsum, curr_psum])
    # loop done
    # restore TL 89, 8E, 81
    wr_test_reg(comm, addr=0x89, data=initval_89)
    wr_test_reg(comm, addr=0x8E, data=initval_8E)
    wr_test_reg(comm, addr=0x81, data=initval_81)
    # Disable test-mode
    tm_exit(comm)
    # convert to dataframe
    if fast is True:
        df = pd.DataFrame(data=ret_list,
                          columns=["prefix", "vt", "csum", "psum"]
                          )
    else:
        df = pd.DataFrame(data=ret_list,
                          columns=["prefix", "vt", "csum", "psum", "hexstring"]
                          )
    # df["addr"] = '0x' + tohex(addr)
    df["addr"] = hex(addr)
    du.echo(comm, 'on')
    if plot:
        df.plot(x='vt', y='psum')
        plt.yscale('log')
        plt.grid()
        # plt.savefig('vt_curve.png')  # CM
        plt.show()
    return df


# *****************************
# *****       MAIN        *****
# *****************************
# Run this module in standalone mode to test functionality
if __name__ == '__main__':
    # *********************
    # *****  Connect  *****
    # *********************
    comm = boardcom.BoardComm()   # create an instance of class BoardComm
    connectedPort = comm.find_and_connect(echo=1)

    du.flash_program(comm)

    get_vt_curves(comm=comm, addr=0, numbytes=0x4000, prefix="", fast=True, nocpsum=False,
                  minvdac=0, maxvdac=63, with_nbias=True, plot=True)

    # ************************
    # *****  Disconnect  *****
    # ************************
    comm.disconnect(connectedPort, echo=1)
